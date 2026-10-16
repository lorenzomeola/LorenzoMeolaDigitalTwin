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
def test_invalid_requirements_or_evidence_fail_closed(requirement):
    from app.role_match import analyze_role

    with pytest.raises(ValueError):
        analyze_role("Required: Python", analysis_client([requirement]))


def test_empty_extraction_does_not_fabricate_zero_percent():
    from app.role_match import analyze_role

    with pytest.raises(ValueError):
        analyze_role("Hello", analysis_client([]))


def test_duplicate_requirements_do_not_inflate_score():
    from app.role_match import analyze_role

    requirement = {"source_quote": "Python", "priority": "required", "match": "not_accredited", "evidence_ids": []}
    with pytest.raises(ValueError):
        analyze_role("Python", analysis_client([requirement, requirement]))


def test_role_tool_rejects_description_not_provided_by_visitor():
    from app.tools import get_skills_for_role

    with pytest.raises(ValueError, match="visitor"):
        get_skills_for_role("Invented job description", visitor_text="Hello")