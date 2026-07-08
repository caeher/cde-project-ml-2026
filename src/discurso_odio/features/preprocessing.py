"""Preprocesamiento de texto en español para clasificación de odio."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, elimina URLs y espacios extra."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def remove_accents(text: str) -> str:
    """Elimina acentos del texto (opcional para ciertos modelos)."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")
