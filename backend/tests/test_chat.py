import os
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


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
    monkeypatch.setattr("backend.app.openai_client.chat.completions.create", create)

    response = client.post("/api/chat", json={"message": "Tell me about your projects"})

    assert response.status_code == 200
    assert response.json() == {"reply": "I build data and AI projects."}
    assert create.call_args.kwargs["tools"] == []


def test_chat_offers_contact_tool_only_after_ui_consent(monkeypatch):
    create = Mock(return_value=model_response("Would you like to share your email?"))
    monkeypatch.setattr("backend.app.openai_client.chat.completions.create", create)

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
    monkeypatch.setattr("backend.app.openai_client.chat.completions.create", create)
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
    monkeypatch.setattr("backend.app.openai_client.chat.completions.create", create)

    response = client.post(
        "/api/chat",
        json={"message": "Please contact me", "contactConsent": True},
    )

    assert response.status_code == 200
    assert create.call_args.kwargs["tools"] == []


def test_chat_rejects_blank_messages():
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_rejects_oversized_messages():
    response = client.post("/api/chat", json={"message": "x" * 4001})

    assert response.status_code == 422