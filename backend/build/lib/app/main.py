import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

import truststore
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, model_validator

from app.context import system_prompt
from app.tools import TOOLS, handle_tool_calls

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
    return OpenAI(api_key=api_key, base_url=PROVIDERS[provider]["base_url"], timeout=60)


def client_for(provider):
    api_key = os.getenv(PROVIDERS[provider]["key_env"])
    return _build_client(provider, api_key) if api_key else None


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
    message: str = Field(min_length=1, max_length=4000)
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
def chat(request: ChatRequest):
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
    available_tools = TOOLS if request.contactConsent and visitor_emails else []
    options = completion_options(request.provider, request.model, available_tools)

    try:
        response = client.chat.completions.create(messages=messages, **options)
        tool_rounds = 0
        while response.choices[0].finish_reason == "tool_calls":
            if not request.contactConsent or tool_rounds >= 3:
                raise RuntimeError("Tool call is not allowed or exceeded the limit")

            assistant_message = response.choices[0].message
            messages.append(assistant_message)
            messages.extend(
                handle_tool_calls(
                    assistant_message.tool_calls,
                    consent_confirmed=request.contactConsent,
                    visitor_emails=visitor_emails,
                )
            )
            response = client.chat.completions.create(messages=messages, **options)
            tool_rounds += 1

        reply = response.choices[0].message.content
        if not reply:
            raise RuntimeError("The model returned an empty reply")
        return ChatResponse(reply=reply)
    except HTTPException:
        raise
    except Exception as error:
        logger.warning("Chat request failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="The chat service is temporarily unavailable",
        ) from error