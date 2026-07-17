"""Pruebas de preprocesamiento de texto."""

from discurso_odio.features.preprocessing import anonymize_text, normalize_text


def test_normalize_text_removes_urls():
    text = "Mira esto https://example.com ahora"
    assert "http" not in normalize_text(text)


def test_anonymize_text_replaces_mentions():
    text = "@usuario hola mundo"
    result = anonymize_text(text)
    assert "@usuario" not in result
    assert "[USUARIO]" in result
