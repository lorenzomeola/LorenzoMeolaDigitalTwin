import logging
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

import truststore
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, model_validator

from app.context import system_prompt
from app.guardrails import CONTACT_FAILED_REPLY, CONTACT_SAVED_REPLY, guard_reply
from app.rate_limit import enforce_rate_limit
from app.tools import WRITE_TOOLS, available_tools, handle_tool_calls

# Corporate networks re-sign TLS traffic; the OS trust store lets provider calls verify.
truststore.inject_into_ssl()

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")
load_dotenv(REPOSITORY_ROOT / ".env.local", override=True)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Only these models are reachable, so a visitor cannot pick an expensive one.
PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "key_env": "OPENAI_API_KEY",
        "base_url": None,
        "token_param": "max_completion_tokens",
        "models": ["gpt-5.4-nano", "gpt-4.1-mini"],
    },
    "groq": {
        "label": "Groq",
        "key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "token_param": "max_completion_tokens",
        "models": ["openai/gpt-oss-20b"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "token_param": "max_tokens",
        "models": ["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-31b-it:free"],
    },
}
MAX_REPLY_TOKENS = 2000


@lru_cache(maxsize=8)
def _build_client(provider, api_key):
    return OpenAI(api_key=api_key, base_url=PROVIDERS[provider]["base_url"], timeout=30, max_retries=0)


def client_for(provider):
    api_key = os.getenv(PROVIDERS[provider]["key_env"])
    return _build_client(provider, api_key) if api_key else None


@lru_cache(maxsize=2)
def _build_review_client(api_key):
    return OpenAI(api_key=api_key, timeout=12, max_retries=0)


def review_client():
    api_key = os.getenv("OPENAI_API_KEY")
    return _build_review_client(api_key) if api_key else None


def configured_providers():
    return [
        {"id": provider_id, "label": spec["label"], "models": spec["models"]}
        for provider_id, spec in PROVIDERS.items()
        if os.getenv(spec["key_env"])
    ]


def completion_options(provider, model, tools):
    options = {"model": model, PROVIDERS[provider]["token_param"]: MAX_REPLY_TOKENS}
    if tools:
        options["tools"] = tools
    return options


email_pattern = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+", re.I)

app = FastAPI(title="Lorenzo Meola Digital Twin API", version="1.0.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Message content cannot be blank")
        return value


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)
    contactConsent: bool = False
    provider: str = "openai"
    model: str | None = None

    @model_validator(mode="after")
    def provider_and_model_must_be_allowed(self):
        spec = PROVIDERS.get(self.provider)
        if spec is None:
            raise ValueError("Unknown provider")
        if self.model is None:
            self.model = spec["models"][0]
        elif self.model not in spec["models"]:
            raise ValueError("Model is not available for this provider")
        return self

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/providers")
def providers():
    available = configured_providers()
    default = (
        {"provider": available[0]["id"], "model": available[0]["models"][0]}
        if available
        else None
    )
    return {"providers": available, "default": default}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    enforce_rate_limit(http_request.headers.get("x-twin-client-ip", "unknown"))
    client = client_for(request.provider)
    if client is None:
        raise HTTPException(status_code=503, detail="The chat service is not configured")

    messages = [
        {"role": "system", "content": system_prompt(request.contactConsent)},
        *[message.model_dump() for message in request.history],
        {"role": "user", "content": request.message},
    ]
    visitor_text = " ".join(
        message["content"] for message in messages if message["role"] == "user"
    )
    visitor_emails = set(email_pattern.findall(visitor_text))
    offered_tools = available_tools(request.contactConsent, visitor_emails)
    options = completion_options(request.provider, request.model, offered_tools)

    try:
        response = client.chat.completions.create(messages=messages, **options)
        if response.choices[0].finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            if (
                len(tool_calls) != 1
                or tool_calls[0].function.name not in {tool["function"]["name"] for tool in offered_tools}
            ):
                raise RuntimeError("Tool call is not allowed")
            results = handle_tool_calls(
                tool_calls,
                consent_confirmed=request.contactConsent,
                visitor_emails=visitor_emails,
                visitor_text=visitor_text,
                current_message=request.message,
                analysis_client=review_client(),
            )
            tool_name = tool_calls[0].function.name
            result = json.loads(results[0]["content"]) if results else {"status": "error"}
            if tool_name in WRITE_TOOLS:
                confirmations = {
                    "record_user_details": CONTACT_SAVED_REPLY,
                    "request_interview": "Your interview request has been saved for Lorenzo. This is not a confirmed booking; the preferred time is a request only.",
                    "leave_message": "Your message has been saved for Lorenzo. No automatic notification has been sent.",
                }
                return ChatResponse(reply=confirmations[tool_name] if result.get("status") == "saved" else CONTACT_FAILED_REPLY)
            if result.get("status") != "ok":
                return ChatResponse(reply="I couldn't retrieve that information right now. Please try again with the full details.")
            if tool_name == "get_contact_details":
                return ChatResponse(reply=(
                    f"Lorenzo Meola\n\nEmail: {result['email']}\n\nPhone: {result['phone']}\n\nLocation: {result['location']}"
                ))
            from app.role_match import render_analysis

            return ChatResponse(reply=guard_reply(
                render_analysis(result), request.message, review_client(), verified_analysis=result,
            ))

        reply = response.choices[0].message.content
        if not reply:
            raise RuntimeError("The model returned an empty reply")
        return ChatResponse(reply=guard_reply(reply, request.message, review_client()))
    except HTTPException:
        raise
    except Exception as error:
        logger.warning("Chat request failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="The chat service is temporarily unavailable",
        ) from error