import os
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr("app.main.enforce_rate_limit", Mock(), raising=False)
    monkeypatch.setattr("app.main.review_client", lambda: None, raising=False)
    monkeypatch.setattr("app.main.guard_reply", lambda draft, *args, **kwargs: draft, raising=False)


def use_client(monkeypatch, create):
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr("app.main.client_for", lambda provider: fake_client)


def model_response(text):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content=text, tool_calls=None),
            )
        ]
    )


def test_health_endpoint_reports_ready():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_model_reply_without_contact_consent(monkeypatch):
    create = Mock(return_value=model_response("I build data and AI projects."))
    use_client(monkeypatch, create)

    response = client.post("/api/chat", json={"message": "Tell me about your projects"})

    assert response.status_code == 200
    assert response.json() == {"reply": "I build data and AI projects."}
    assert {tool["function"]["name"] for tool in create.call_args.kwargs["tools"]} == {
        "get_contact_details", "get_skills_for_role",
    }


def test_chat_offers_contact_tool_only_after_ui_consent(monkeypatch):
    create = Mock(return_value=model_response("Would you like to share your email?"))
    use_client(monkeypatch, create)

    response = client.post(
        "/api/chat",
        json={
            "message": "Please contact me at candidate@example.com",
            "contactConsent": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Would you like to share your email?"
    assert {tool["function"]["name"] for tool in create.call_args.kwargs["tools"]} == {
        "record_user_details", "request_interview", "leave_message", "get_contact_details", "get_skills_for_role",
    }


def test_chat_runs_tool_call_and_returns_follow_up_reply(monkeypatch):
    tool_call = SimpleNamespace(
        id="call_contact",
        function=SimpleNamespace(
            name="record_user_details",
            arguments='{"email":"candidate@example.com"}',
        ),
    )
    tool_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="tool_calls",
                message=SimpleNamespace(content=None, tool_calls=[tool_call]),
            )
        ]
    )
    create = Mock(
        side_effect=[tool_response, model_response("Thanks, I have saved your contact details.")]
    )
    dispatch = Mock(return_value=[{"role": "tool", "content": '{"status":"saved"}', "tool_call_id": "call_contact"}])
    use_client(monkeypatch, create)
    monkeypatch.setattr("app.main.handle_tool_calls", dispatch)

    response = client.post(
        "/api/chat",
        json={
            "message": "Please contact me at candidate@example.com",
            "contactConsent": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Your contact details have been saved for Lorenzo to follow up."
    dispatch.assert_called_once_with(
        [tool_call],
        consent_confirmed=True,
        visitor_emails={"candidate@example.com"},
        visitor_text="Please contact me at candidate@example.com",
        current_message="Please contact me at candidate@example.com",
        analysis_client=None,
    )
    assert create.call_count == 1


def test_chat_does_not_offer_contact_tool_without_visitor_email(monkeypatch):
    create = Mock(return_value=model_response("Please share your email address."))
    use_client(monkeypatch, create)

    response = client.post(
        "/api/chat",
        json={"message": "Please contact me", "contactConsent": True},
    )

    assert response.status_code == 200
    assert {tool["function"]["name"] for tool in create.call_args.kwargs["tools"]} == {
        "get_contact_details", "get_skills_for_role",
    }


def test_chat_accepts_long_assistant_replies_in_history(monkeypatch):
    create = Mock(return_value=model_response("Sure."))
    use_client(monkeypatch, create)
    long_reply = "word " * 2400

    response = client.post(
        "/api/chat",
        json={
            "message": "And the second one?",
            "history": [
                {"role": "user", "content": "Tell me about your projects"},
                {"role": "assistant", "content": long_reply},
            ],
        },
    )

    assert response.status_code == 200


def test_chat_tells_the_model_whether_the_visitor_ticked_the_consent_box(monkeypatch):
    create = Mock(return_value=model_response("Noted."))
    use_client(monkeypatch, create)

    client.post("/api/chat", json={"message": "Hello", "contactConsent": True})
    ticked = create.call_args.kwargs["messages"][0]["content"]
    client.post("/api/chat", json={"message": "Hello", "contactConsent": False})
    unticked = create.call_args.kwargs["messages"][0]["content"]

    assert "ticked the consent box" in ticked
    assert "has not ticked the consent box" in unticked
    assert "has not ticked the consent box" not in ticked


def test_chat_rejects_blank_messages():
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_rejects_oversized_messages():
    response = client.post("/api/chat", json={"message": "x" * 12001})

    assert response.status_code == 422


def test_providers_lists_only_configured_providers_without_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-openai")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-secret-groq")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    response = client.get("/api/providers")

    assert response.status_code == 200
    body = response.json()
    assert [provider["id"] for provider in body["providers"]] == ["openai", "groq"]
    assert body["default"] == {"provider": "openai", "model": "gpt-5.4-nano"}
    assert "secret" not in response.text


def test_openrouter_only_offers_free_models():
    from app.main import PROVIDERS

    models = PROVIDERS["openrouter"]["models"]

    assert models
    assert all(model.endswith(":free") for model in models)


def test_chat_uses_the_selected_provider_and_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    create = Mock(return_value=model_response("Hello from Groq"))
    use_client(monkeypatch, create)

    response = client.post(
        "/api/chat",
        json={"message": "Hi", "provider": "groq", "model": "openai/gpt-oss-20b"},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "Hello from Groq"}
    assert create.call_args.kwargs["model"] == "openai/gpt-oss-20b"


def test_chat_rejects_unknown_providers_and_unlisted_models():
    unknown_provider = client.post(
        "/api/chat", json={"message": "Hi", "provider": "made-up"}
    )
    unlisted_model = client.post(
        "/api/chat", json={"message": "Hi", "provider": "openai", "model": "gpt-expensive"}
    )

    assert unknown_provider.status_code == 422
    assert unlisted_model.status_code == 422


def test_chat_reports_unconfigured_provider(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = client.post("/api/chat", json={"message": "Hi", "provider": "groq"})

    assert response.status_code == 503


def test_chat_rate_limit_rejects_before_any_model_call(monkeypatch):
    limit = Mock(side_effect=HTTPException(
        status_code=429, detail="Too many messages", headers={"Retry-After": "45"},
    ))
    model_client = Mock()
    monkeypatch.setattr("app.main.enforce_rate_limit", limit)
    monkeypatch.setattr("app.main.client_for", model_client)

    response = client.post(
        "/api/chat", json={"message": "Hello"}, headers={"x-twin-client-ip": "192.0.2.1"},
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "45"
    limit.assert_called_once_with("192.0.2.1")
    model_client.assert_not_called()


def test_chat_returns_only_filtered_reply(monkeypatch):
    create = Mock(return_value=model_response("An unsafe draft"))
    use_client(monkeypatch, create)
    guard = Mock(return_value="A safe reply")
    monkeypatch.setattr("app.main.guard_reply", guard)

    response = client.post("/api/chat", json={"message": "Tell me about Lorenzo"})

    assert response.json() == {"reply": "A safe reply"}
    guard.assert_called_once_with("An unsafe draft", "Tell me about Lorenzo", None)


def test_chat_confirms_failed_storage_from_tool_result_not_model_claim(monkeypatch):
    tool_call = SimpleNamespace(
        id="call_failed", function=SimpleNamespace(
            name="record_user_details", arguments='{"email":"candidate@example.com"}',
        ),
    )
    response_with_tool = SimpleNamespace(choices=[SimpleNamespace(
        finish_reason="tool_calls", message=SimpleNamespace(tool_calls=[tool_call]),
    )])
    create = Mock(return_value=response_with_tool)
    use_client(monkeypatch, create)
    monkeypatch.setattr("app.main.handle_tool_calls", Mock(return_value=[{
        "role": "tool", "content": json.dumps({"status": "error"}), "tool_call_id": "call_failed",
    }]))

    response = client.post("/api/chat", json={
        "message": "Save candidate@example.com", "contactConsent": True,
    })

    assert response.json()["reply"] == "I couldn't save your contact details right now. Please try again later."
    assert create.call_count == 1


def test_chat_returns_authorized_contact_details_without_consent(monkeypatch):
    from app.context import PUBLIC_CONTACT_DETAILS

    tool_call = SimpleNamespace(id="contact", function=SimpleNamespace(name="get_contact_details", arguments="{}"))
    create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(
        finish_reason="tool_calls", message=SimpleNamespace(tool_calls=[tool_call]),
    )]))
    use_client(monkeypatch, create)

    response = client.post("/api/chat", json={"message": "How can I contact Lorenzo?"})

    assert response.status_code == 200
    assert PUBLIC_CONTACT_DETAILS["email"] in response.json()["reply"]
    assert PUBLIC_CONTACT_DETAILS["phone"] in response.json()["reply"]
    assert "Ghent, Belgium" in response.json()["reply"]


@pytest.mark.parametrize("tool_name,expected", [
    ("request_interview", "not a confirmed booking"),
    ("leave_message", "message has been saved"),
])
def test_chat_confirms_new_write_tools_from_storage_result(monkeypatch, tool_name, expected):
    tool_call = SimpleNamespace(id="write", function=SimpleNamespace(name=tool_name, arguments="{}"))
    create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(
        finish_reason="tool_calls", message=SimpleNamespace(tool_calls=[tool_call]),
    )]))
    use_client(monkeypatch, create)
    monkeypatch.setattr("app.main.handle_tool_calls", Mock(return_value=[{
        "role": "tool", "content": '{"status":"saved"}', "tool_call_id": "write",
    }]))

    response = client.post("/api/chat", json={"message": "Contact me at candidate@example.com", "contactConsent": True})

    assert response.status_code == 200
    assert expected in response.json()["reply"]


def test_chat_accepts_pasted_role_descriptions_up_to_12000_characters(monkeypatch):
    create = Mock(return_value=model_response("A role analysis needs specific requirements."))
    use_client(monkeypatch, create)

    assert client.post("/api/chat", json={"message": "Python " * 1000}).status_code == 200