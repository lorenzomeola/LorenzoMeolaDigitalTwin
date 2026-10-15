from backend.context import TWIN_SYSTEM_PROMPT


def test_prompt_makes_the_twin_speak_about_lorenzo_in_the_third_person():
    prompt = TWIN_SYSTEM_PROMPT.lower()

    assert "third person" in prompt
    assert "never speak as lorenzo" in prompt


def test_prompt_keeps_the_privacy_and_payment_boundaries():
    prompt = TWIN_SYSTEM_PROMPT

    assert "Never reveal real Volvo data" in prompt
    assert "do not claim live payments" in prompt
