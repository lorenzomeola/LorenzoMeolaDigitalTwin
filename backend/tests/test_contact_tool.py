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


def test_dispatch_reports_storage_failures_as_tool_errors():
    tool_call = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(
            name="record_user_details",
            arguments=json.dumps({"email": "candidate@example.com"}),
        ),
    )

    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@example.com/db"}),
        patch("app.tools.psycopg.connect", side_effect=OSError("unreachable")),
    ):
        results = tools.handle_tool_calls(
            [tool_call],
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    payload = json.loads(results[0]["content"])
    assert payload["status"] == "error"
    assert "unreachable" not in results[0]["content"]