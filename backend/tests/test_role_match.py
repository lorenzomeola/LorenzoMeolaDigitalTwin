import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


def analysis_client(requirements):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content=json.dumps({"requirements": requirements}),
    ))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(return_value=response))))


def test_score_is_computed_from_validated_evidence_not_model_percentage():
    from app.role_match import VERIFIED_FACTS, analyze_role

    fact_id = next(iter(VERIFIED_FACTS))
    requirements = [
        {"source_quote": "Python", "priority": "required", "match": "covered", "evidence_ids": [fact_id]},
        {"source_quote": "React", "priority": "required", "match": "partial", "evidence_ids": [fact_id]},
        {"source_quote": "Kubernetes", "priority": "preferred", "match": "not_accredited", "evidence_ids": []},
    ]
    client = analysis_client(requirements)

    result = analyze_role("Required: Python and React. Preferred: Kubernetes.", client)

    assert result["coverage_percent"] == 60
    assert result["requirements"][0]["evidence"] == [VERIFIED_FACTS[fact_id]]
    assert "not a hiring probability" in result["methodology"]
    assert "tools" not in client.chat.completions.create.call_args.kwargs
    assert "one atomic requirement per entry" in client.chat.completions.create.call_args.kwargs["messages"][0]["content"]


@pytest.mark.parametrize("requirement", [
    {"source_quote": "Invented requirement", "priority": "required", "match": "not_accredited", "evidence_ids": []},
    {"source_quote": "Python", "priority": "required", "match": "covered", "evidence_ids": ["invented"]},
    {"source_quote": "Python", "priority": "required", "match": "covered", "evidence_ids": []},
])
def test_invalid_requirements_or_evidence_fail_closed(requirement, caplog):
    from app.role_match import analyze_role

    with pytest.raises(ValueError):
        analyze_role("AI Engineer role. Required: Python.", analysis_client([requirement]))
    assert "role_analysis_rejected code=" in caplog.text
    assert "Required: Python" not in caplog.text


def test_empty_extraction_does_not_fabricate_zero_percent():
    from app.role_match import analyze_role

    with pytest.raises(ValueError):
        analyze_role("A role with unclear duties.", analysis_client([]))


def test_duplicate_requirements_do_not_inflate_score():
    from app.role_match import analyze_role

    requirement = {"source_quote": "Python", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    result = analyze_role("AI role requiring Python.", analysis_client([requirement, requirement]))
    assert len(result["requirements"]) == 1


def test_retry_feedback_names_the_invalid_quote():
    from app.role_match import analyze_role

    invalid = {"source_quote": "use CI/CD", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    valid = {"source_quote": "CI/CD", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    client = analysis_client([invalid])
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"requirements": [item]})))])
        for item in (invalid, valid)
    ]

    analyze_role("Required: use Docker and CI/CD", client)

    assert "use CI/CD" in client.chat.completions.create.call_args.kwargs["messages"][0]["content"]


def test_role_tool_rejects_description_not_provided_by_visitor():
    from app.tools import get_skills_for_role

    with pytest.raises(ValueError, match="visitor"):
        get_skills_for_role("Invented job description", visitor_text="Hello")


def test_invalid_quote_gets_one_corrected_extraction_without_relaxing_validation():
    from app.role_match import analyze_role

    invalid = {"source_quote": "Invented requirement", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    valid = {"source_quote": "Python", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    client = analysis_client([invalid])
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"requirements": [item]})))])
        for item in (invalid, valid)
    ]

    result = analyze_role("AI Engineer role. Required: Python.", client)

    assert result["coverage_percent"] == 0
    assert result["requirements"][0]["requirement"] == "Python"
    assert client.chat.completions.create.call_count == 2


def test_repeated_invalid_extraction_is_bounded_and_still_rejected():
    from app.role_match import analyze_role

    invalid = {"source_quote": "Invented requirement", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    client = analysis_client([invalid])
    with pytest.raises(ValueError):
        analyze_role("AI Engineer role. Required: Python.", client)
    assert client.chat.completions.create.call_count == 2