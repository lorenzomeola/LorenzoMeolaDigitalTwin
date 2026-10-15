import os
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from backend import tools


def test_model_tool_schema_does_not_accept_consent_as_an_argument():
    properties = tools.RECORD_USER_DETAILS_SCHEMA["parameters"]["properties"]

    assert "consent_confirmed" not in properties


def test_contact_tool_saves_only_after_consent():
    client = Mock()
    table = client.table.return_value
    table.insert.return_value.execute.return_value.data = [{"id": 1}]

    with (
        patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
            },
        ),
        patch("backend.tools.create_client", return_value=client),
    ):
        result = tools.record_user_details(
            email=" candidate@example.com ",
            name="Candidate",
            notes="Interested in an AI Engineer role",
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )

    assert result == {"status": "saved"}
    client.table.assert_called_once_with("twin_contact_requests")
    inserted = table.insert.call_args.args[0]
    assert inserted["email"] == "candidate@example.com"
    assert inserted["name"] == "Candidate"
    assert inserted["notes"] == "Interested in an AI Engineer role"
    assert inserted["consent_confirmed_at"]


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

    with pytest.raises(ValueError, match="provided by the visitor"):
        tools.handle_tool_calls(
            [tool_call],
            consent_confirmed=True,
            visitor_emails={"candidate@example.com"},
        )