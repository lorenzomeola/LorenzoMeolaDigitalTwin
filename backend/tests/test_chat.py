import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")


def use_client(monkeypatch, create):
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr("backend.app.client_for", lambda provider: fake_client)


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
    assert "tools" not in create.call_args.kwargs


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
    assert [tool["function"]["name"] for tool in create.call_args.kwargs["tools"]] == [
        "record_user_details"
    ]


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
    dispatch = Mock(return_value=[])
    use_client(monkeypatch, create)
    monkeypatch.setattr("backend.app.handle_tool_calls", dispatch)

    response = client.post(
        "/api/chat",
        json={
            "message": "Please contact me at candidate@example.com",
            "contactConsent": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Thanks, I have saved your contact details."
    dispatch.assert_called_once_with(
        [tool_call],
        consent_confirmed=True,
        visitor_emails={"candidate@example.com"},
    )
    assert create.call_count == 2


def test_chat_does_not_offer_contact_tool_without_visitor_email(monkeypatch):
    create = Mock(return_value=model_response("Please share your email address."))
    use_client(monkeypatch, create)

    response = client.post(
        "/api/chat",
        json={"message": "Please contact me", "contactConsent": True},
    )

    assert response.status_code == 200
    assert "tools" not in create.call_args.kwargs


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
    response = client.post("/api/chat", json={"message": "x" * 4001})

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