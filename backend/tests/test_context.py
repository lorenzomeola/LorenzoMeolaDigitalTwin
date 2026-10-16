import json
from pathlib import Path

from app.context import TWIN_SYSTEM_PROMPT

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_frontend_and_backend_share_identical_content():
    for name in ("profile.json", "projects.json"):
        backend_copy = json.loads((REPOSITORY_ROOT / "backend" / "content" / name).read_text(encoding="utf-8"))
        frontend_copy = json.loads((REPOSITORY_ROOT / "frontend" / "content" / name).read_text(encoding="utf-8"))

        assert backend_copy == frontend_copy, f"{name} differs between backend/content and frontend/content"


def test_prompt_states_the_confirmed_ownership_of_personal_projects():
    assert "sole developer and owner of AI Assets" in TWIN_SYSTEM_PROMPT
    assert "remains unconfirmed" not in TWIN_SYSTEM_PROMPT


def test_prompt_makes_the_twin_speak_about_lorenzo_in_the_third_person():
    prompt = TWIN_SYSTEM_PROMPT.lower()

    assert "third person" in prompt
    assert "never speak as lorenzo" in prompt


def test_prompt_keeps_the_privacy_and_payment_boundaries():
    prompt = TWIN_SYSTEM_PROMPT

    assert "Never reveal real Volvo data" in prompt
    assert "do not claim live payments" in prompt


def test_prompt_answers_recruiters_without_unsolicited_cv_services():
    assert "recruiters and hiring managers" in TWIN_SYSTEM_PROMPT
    assert "Do not offer to rewrite, tailor, reformat" in TWIN_SYSTEM_PROMPT
    assert "Stop once the question is answered" in TWIN_SYSTEM_PROMPT
    assert "Explicitly requested summaries" in TWIN_SYSTEM_PROMPT
    assert "ask the user if they want you to explain" not in TWIN_SYSTEM_PROMPT
