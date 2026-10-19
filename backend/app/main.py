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
from app.guardrails import CONTACT_FAILED_REPLY, CONTACT_SAVED_REPLY, SAFE_REPLY, guard_reply
from app.localize import localize
from app.rate_limit import enforce_rate_limit
from app.role_match import analysis_labels, render_analysis, summarize_analysis
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
        "models": ["gpt-4.1-mini", "gpt-5.4-nano"],
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
# A question about fit is not a pasted job description; smaller models call the tool anyway.
MIN_ROLE_DESCRIPTION_CHARS = 200


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


def missing_field_reply(reason):
    match = re.search(r"Invalid (\w+)|provide (\w+)", reason or "")
    if "email" in (reason or "").lower() and not match:
        return "I need a valid email address in your message before I can save this."
    if match:
        field = (match.group(1) or match.group(2)).replace("_", " ")
        return f"I still need your {field}, exactly as you want it saved, before I can save this. Please send it in your next message."
    return None


SAVE_CONFIRMATIONS = {
    "record_user_details": CONTACT_SAVED_REPLY,
    "request_interview": "Your interview request has been saved for Lorenzo. This is not a confirmed booking; the preferred time is a request only. He will review it and contact you directly to arrange the details.",
    "leave_message": "Your message has been saved for Lorenzo. He will review it and contact you directly.",
}


def tool_text(tool_name, result):
    if tool_name in WRITE_TOOLS:
        if result.get("status") == "saved":
            return SAVE_CONFIRMATIONS[tool_name]
        return missing_field_reply(result.get("reason")) or CONTACT_FAILED_REPLY
    if result.get("status") != "ok":
        if tool_name == "get_skills_for_role":
            return (
                "I couldn't analyze that job description. Please try again, ideally pasting only "
                "the responsibilities and requirements as plain text."
            )
        return "I couldn't retrieve that information right now. Please try again with the full details."
    return f"Lorenzo Meola\n\nEmail: {result['email']}\n\nPhone: {result['phone']}\n\nLocation: {result['location']}"


def tool_reply(tool_results, question, visitor_text):
    strings, plan = {}, []
    reviewer = review_client()
    for index, (tool_name, result) in enumerate(tool_results):
        if tool_name == "get_skills_for_role" and result.get("status") == "ok":
            plan.append(("analysis", index, result))
            continue
        text = tool_text(tool_name, result)
        strings[str(index)] = text
        plan.append(("text", index, None))
    translated = localize(strings, visitor_text, reviewer)
    parts = []
    for kind, index, result in plan:
        if kind == "text":
            parts.append(translated[str(index)])
        else:
            try:
                summary = summarize_analysis(result, visitor_text, reviewer)
                labels = localize(analysis_labels(result), summary, reviewer)
                draft = render_analysis(result, summary, labels)
                reply = guard_reply(draft, question, reviewer, verified_analysis=result, visitor_text=visitor_text)
            except Exception as error:
                logger.warning("role_summary_failed error_type=%s", type(error).__name__)
                reply = SAFE_REPLY
            if reply == SAFE_REPLY:
                reply = localize({"reply": SAFE_REPLY}, visitor_text, reviewer)["reply"]
            parts.append(reply)
    return "\n\n".join(parts)


email_pattern = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+", re.I)
# Smaller models call get_contact_details for unrelated questions, so the visitor must ask for contact data.
contact_intent = re.compile(
    r"e-?mail|mail\b|phone|telephone|mobile|\bcall\b|\bnumber\b|contact|reach|get in touch|"
    r"correo|tel[eé]fono|n[uú]mero|llamar|contactar|contatt|telefon|numero|chiamare",
    re.I,
)

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
    history: list[HistoryMessage] = Field(default_factory=list, max_length=40)
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
        tool_calls = []
        if response.choices[0].finish_reason == "tool_calls":
            allowed = {tool["function"]["name"] for tool in offered_tools}
            if any(call.function.name not in allowed for call in response.choices[0].message.tool_calls):
                raise RuntimeError("Tool call is not allowed")
            seen = set()
            for call in response.choices[0].message.tool_calls:
                if call.function.name in seen:
                    continue
                if call.function.name == "get_contact_details" and not contact_intent.search(request.message):
                    continue
                if call.function.name == "get_skills_for_role" and len(request.message.strip()) < MIN_ROLE_DESCRIPTION_CHARS:
                    continue
                seen.add(call.function.name)
                tool_calls.append(call)
            if not tool_calls:
                response = client.chat.completions.create(
                    messages=messages, **completion_options(request.provider, request.model, None),
                )
        if tool_calls:
            results = handle_tool_calls(
                tool_calls,
                consent_confirmed=request.contactConsent,
                visitor_emails=visitor_emails,
                visitor_text=visitor_text,
                current_message=request.message,
                analysis_client=review_client(),
            )
            parts = [
                (call.function.name, json.loads(item["content"]))
                for call, item in zip(tool_calls, results)
            ]
            return ChatResponse(reply=tool_reply(parts, request.message, visitor_text))

        reply = response.choices[0].message.content
        if not reply:
            raise RuntimeError("The model returned an empty reply")
        reply = guard_reply(reply, request.message, review_client(), visitor_text=visitor_text)
        if reply == SAFE_REPLY:
            reply = localize({"reply": SAFE_REPLY}, visitor_text, review_client())["reply"]
        return ChatResponse(reply=reply)
    except HTTPException:
        raise
    except Exception as error:
        logger.warning("Chat request failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="The chat service is temporarily unavailable",
        ) from error