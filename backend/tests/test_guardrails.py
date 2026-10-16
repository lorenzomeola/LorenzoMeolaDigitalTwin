import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


def completion(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def reviewer(*responses):
    create = Mock(side_effect=[completion(response) for response in responses])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_contact_information_is_removed_from_model_context():
    from app.context import redact_contacts

    text = redact_contacts("Contact: owner@example.com. Phone: +32 470 12 34 56")

    assert "owner@example.com" not in text
    assert "470" not in text


def test_approved_reply_passes_without_tools():
    from app.guardrails import guard_reply

    client = reviewer(json.dumps({"approved": True, "violations": []}))
    draft = "Lorenzo is the sole developer and owner of MatchKeeper."

    assert guard_reply(draft, "Who built MatchKeeper?", client) == draft
    options = client.chat.completions.create.call_args.kwargs
    assert "tools" not in options
    assert options["model"] == "gpt-4.1-mini"


@pytest.mark.parametrize("draft", [
    "Email Lorenzo at owner@example.com",
    "Call +32 470 12 34 56",
    "I saved your email.",
    "Visit https://internal.volvo.example/reports",
    "Go to https://untrusted.example/lorenzo",
])
def test_deterministic_checks_block_without_calling_reviewer(draft):
    from app.guardrails import SAFE_REPLY, guard_reply

    client = reviewer()

    assert guard_reply(draft, "Give me his contact details", client) == SAFE_REPLY
    client.chat.completions.create.assert_not_called()


def test_rejected_reply_is_repaired_and_reviewed_again():
    from app.guardrails import guard_reply

    client = reviewer(
        json.dumps({"approved": False, "violations": ["unsupported_claim"]}),
        "MatchKeeper's paid bookings are inactive and sandbox-tested only.",
        json.dumps({"approved": True, "violations": []}),
    )

    result = guard_reply("MatchKeeper processes live payments.", "Are payments live?", client)

    assert "inactive" in result
    assert client.chat.completions.create.call_count == 3
    assert all("tools" not in call.kwargs for call in client.chat.completions.create.call_args_list)


@pytest.mark.parametrize("response", [
    "not json",
    '{"approved": "true", "violations": []}',
    '{"approved": true, "violations": ["unsupported_claim"]}',
])
def test_invalid_reviewer_output_fails_closed(response):
    from app.guardrails import SAFE_REPLY, guard_reply

    assert guard_reply("Lorenzo builds AI products.", "What does he do?", reviewer(response)) == SAFE_REPLY


def test_unavailable_reviewer_fails_closed():
    from app.guardrails import SAFE_REPLY, guard_reply

    assert guard_reply("A draft", "A question", None) == SAFE_REPLY


def test_reviewer_timeout_never_exposes_draft():
    from app.guardrails import SAFE_REPLY, guard_reply

    client = reviewer()
    client.chat.completions.create.side_effect = TimeoutError("private draft")

    assert guard_reply("A draft", "A question", client) == SAFE_REPLY


def test_failed_second_review_returns_safe_reply():
    from app.guardrails import SAFE_REPLY, guard_reply

    client = reviewer(
        '{"approved": false, "violations": ["unsupported_claim"]}',
        "Another unsupported claim",
        '{"approved": false, "violations": ["unsupported_claim"]}',
    )

    assert guard_reply("An unsupported claim", "A question", client) == SAFE_REPLY
    assert client.chat.completions.create.call_count == 3


def test_verified_public_link_is_allowed():
    from app.guardrails import guard_reply

    draft = "Lorenzo's LinkedIn: https://www.linkedin.com/in/lmv14/"
    client = reviewer('{"approved": true, "violations": []}')

    assert guard_reply(draft, "Where can I contact Lorenzo?", client) == draft


def test_reviewer_and_repair_remove_unsolicited_cv_offers():
    from app.guardrails import guard_reply

    corrected = "Lorenzo is the sole developer and owner of AI Assets Directory."
    client = reviewer(
        '{"approved": false, "violations": ["style"]}',
        corrected,
        '{"approved": true, "violations": []}',
    )
    draft = corrected + " Would you like me to tailor his CV for a technical role?"

    assert guard_reply(draft, "Tell me about his projects", client) == corrected
    calls = client.chat.completions.create.call_args_list
    policy = calls[0].kwargs["messages"][0]["content"]
    repair = calls[1].kwargs["messages"][0]["content"]
    assert "unsolicited CV rewriting" in policy
    assert "unnecessary closing questions" in policy
    assert "Explicitly requested summaries" in policy
    assert "Remove unsolicited offers" in repair


def test_owner_authorized_contact_details_pass_the_filter():
    from app.context import PUBLIC_CONTACT_DETAILS
    from app.guardrails import guard_reply

    draft = f"Email: {PUBLIC_CONTACT_DETAILS['email']}. Phone: {PUBLIC_CONTACT_DETAILS['phone']}. Location: Ghent, Belgium."
    client = reviewer('{"approved": true, "violations": []}')

    assert guard_reply(draft, "How do I contact Lorenzo?", client) == draft
    policy = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "owner-authorized public contact" in policy


def test_rejected_role_analysis_is_not_rewritten_with_a_model_generated_score():
    from app.guardrails import SAFE_REPLY, guard_reply

    client = reviewer('{"approved": false, "violations": ["unsupported_claim"]}')

    assert guard_reply("Estimated coverage: 80%", "Python role", client,
                       verified_analysis={"coverage_percent": 80}) == SAFE_REPLY
    assert client.chat.completions.create.call_count == 1