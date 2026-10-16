import os
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from app import tools


def test_model_tool_schema_does_not_accept_consent_as_an_argument():
    properties = tools.RECORD_USER_DETAILS_SCHEMA["parameters"]["properties"]

    assert "consent_confirmed" not in properties


def test_contact_tool_saves_only_after_consent():
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)

    with (
        patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://test-user:test-password@example.com/test-db",
            },
        ),
        patch("app.tools.psycopg.connect", return_value=connection) as connect,
    ):
        result = tools.record_user_details(
            email=" candidate@example.com ",
            name="Candidate",
            notes="Interested in an AI Engineer role",
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    assert result == {"status": "saved"}
    connect.assert_called_once_with(
        "postgresql://test-user:test-password@example.com/test-db"
    )
    cursor.execute.assert_called_once()
    query, parameters = cursor.execute.call_args.args
    assert "INSERT INTO public.twin_contact_requests" in query
    assert parameters[:3] == (
        "candidate@example.com",
        "Candidate",
        "Interested in an AI Engineer role",
    )
    assert parameters[3]


def test_contact_tool_requires_database_url():
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(RuntimeError, match="DATABASE_URL"),
    ):
        tools.record_user_details(
            email="candidate@example.com",
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )


def test_contact_tool_rejects_missing_consent():
    with pytest.raises(ValueError, match="Explicit consent"):
        tools.record_user_details(
            email="candidate@example.com",
            consent_confirmed=False,
        )


def test_dispatch_rejects_email_not_written_by_the_visitor():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="record_user_details",
            arguments=json.dumps({"email": "invented@example.com"}),
        ),
    )

    with patch("app.tools.psycopg.connect") as connect:
        results = tools.handle_tool_calls(
            [tool_call],
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    connect.assert_not_called()
    assert json.loads(results[0]["content"])["status"] == "error"


def test_dispatch_reports_storage_failures_as_tool_errors(caplog):
    tool_call = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(
            name="record_user_details",
            arguments=json.dumps({"email": "candidate@example.com"}),
        ),
    )

    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@example.com/db"}),
        patch("app.tools.psycopg.connect", side_effect=OSError("secret connection details")),
    ):
        results = tools.handle_tool_calls(
            [tool_call],
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    payload = json.loads(results[0]["content"])
    assert payload["status"] == "error"
    assert "secret connection details" not in results[0]["content"]
    assert "contact_save_failed error_type=OSError sqlstate=none" in caplog.text
    assert "secret connection details" not in caplog.text
    assert "candidate@example.com" not in caplog.text


def test_dispatch_logs_missing_database_configuration(caplog):
    tool_call = SimpleNamespace(
        id="call_missing_database",
        function=SimpleNamespace(
            name="record_user_details",
            arguments=json.dumps({"email": "candidate@example.com"}),
        ),
    )

    with patch.dict(os.environ, {}, clear=True):
        results = tools.handle_tool_calls(
            [tool_call],
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    assert json.loads(results[0]["content"])["status"] == "error"
    assert "contact_save_unconfigured variable=DATABASE_URL" in caplog.text
    assert "candidate@example.com" not in caplog.text


def test_contact_details_are_public_and_match_the_cv():
    from app.context import PUBLIC_CONTACT_DETAILS

    result = tools.get_contact_details()

    assert result == {"status": "ok", **PUBLIC_CONTACT_DETAILS}
    assert result["email"] and result["phone"]
    assert result["location"] == "Ghent, Belgium"


def test_read_tools_are_available_without_storage_consent():
    schemas = tools.available_tools(consent_confirmed=False, visitor_emails=set())
    names = {schema["function"]["name"] for schema in schemas}

    assert names == {"get_contact_details", "get_skills_for_role"}


@pytest.mark.parametrize("tool_name,arguments,table", [
    ("request_interview", {
        "name": "Recruiter", "company": "Example Co", "email": "candidate@example.com",
        "role": "AI Engineer", "message": "Discuss the position", "preferred_time": "Tuesday 14:00 CET",
    }, "twin_interview_requests"),
    ("leave_message", {
        "name": "Recruiter", "email": "candidate@example.com", "message": "Discuss the position",
    }, "twin_messages"),
])
def test_new_write_tools_persist_only_visitor_provided_fields(tool_name, arguments, table):
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)
    visitor_text = " ".join(arguments.values())
    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}),
        patch("app.tools.psycopg.connect", return_value=connection),
    ):
        result = tools.TOOL_MAP[tool_name](
            **arguments, consent_confirmed=True,
            visitor_emails={"candidate@example.com"}, visitor_text=visitor_text,
        )

    assert result["status"] == "saved"
    query, parameters = cursor.execute.call_args.args
    assert table in query
    assert "candidate@example.com" not in query
    assert "candidate@example.com" in parameters
    assert parameters[-1]


@pytest.mark.parametrize("tool_name", ["request_interview", "leave_message"])
def test_new_write_tools_reject_missing_consent(tool_name):
    arguments = {"name": "Recruiter", "email": "candidate@example.com", "message": "Hello"}
    if tool_name == "request_interview":
        arguments.update(company="Example Co", role="AI Engineer")
    with pytest.raises(ValueError, match="consent"):
        tools.TOOL_MAP[tool_name](**arguments, consent_confirmed=False)


def test_message_cannot_be_invented_by_model():
    with patch("app.tools.psycopg.connect") as connect, pytest.raises(ValueError, match="visitor"):
        tools.leave_message(
            name="Recruiter", email="candidate@example.com", message="Invented message",
            consent_confirmed=True, visitor_emails={"candidate@example.com"},
            visitor_text="Recruiter candidate@example.com Hello",
        )
    connect.assert_not_called()


def test_public_tool_dispatch_does_not_require_email_or_consent():
    tool_call = SimpleNamespace(id="public", function=SimpleNamespace(
        name="get_contact_details", arguments="{}",
    ))

    result = json.loads(tools.handle_tool_calls([tool_call])[0]["content"])

    assert result["status"] == "ok"
    assert result["location"] == "Ghent, Belgium"


def test_dispatch_rejects_malformed_arguments_without_crashing():
    tool_call = SimpleNamespace(id="bad", function=SimpleNamespace(
        name="get_contact_details", arguments="not json",
    ))

    result = json.loads(tools.handle_tool_calls([tool_call])[0]["content"])

    assert result["status"] == "error"