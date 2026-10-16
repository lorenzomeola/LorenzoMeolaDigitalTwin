import json
from types import SimpleNamespace
from unittest.mock import Mock


def translator(payload):
    create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]))
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_localize_uses_translation_and_keeps_protected_values():
    from app.localize import localize

    strings = {"a": "Saved for Lorenzo, ref 42", "b": "Email: x@y.com"}
    client = translator({"a": "Guardado para Lorenzo, ref 42", "b": "Correo: other@y.com"})

    result = localize(strings, "hola, quiero dejar un mensaje", client)

    assert result["a"] == "Guardado para Lorenzo, ref 42"
    assert result["b"] == "Email: x@y.com"


def test_localize_falls_back_to_english_when_unavailable_or_invalid():
    from app.localize import localize

    strings = {"a": "Saved"}

    assert localize(strings, "hola", None) == strings
    assert localize(strings, "hola", translator(["not", "a", "dict"])) == strings
    assert localize(strings, "hola", translator({"a": "x" * 500})) == strings
