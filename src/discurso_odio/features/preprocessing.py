"""Preprocesamiento de texto en español para clasificación de odio."""

from __future__ import annotations

import re
import unicodedata

import ftfy
import pandas as pd

URL_PATTERN = re.compile(r"http\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#(\w+)")
EMAIL_PATTERN = re.compile(r"\S+@\S+")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
WHITESPACE_PATTERN = re.compile(r"\s+")


def fix_encoding(text: str) -> str:
    """Corrige mojibake común en textos recolectados."""
    return ftfy.fix_text(text)


def normalize_text(text: str) -> str:
    """Normaliza texto: minúsculas, elimina URLs y espacios extra."""
    if not isinstance(text, str):
        return ""
    text = fix_encoding(text).lower().strip()
    text = URL_PATTERN.sub(" ", text)
    text = MENTION_PATTERN.sub(" ", text)
    text = HASHTAG_PATTERN.sub(r"\1", text)
    text = EMAIL_PATTERN.sub(" ", text)
    text = PHONE_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def remove_accents(text: str) -> str:
    """Elimina acentos del texto (opcional para ciertos modelos)."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def anonymize_text(text: str) -> str:
    """Anonimiza menciones, URLs y correos en el texto."""
    if not isinstance(text, str):
        return ""
    text = fix_encoding(text)
    text = URL_PATTERN.sub("[URL]", text)
    text = MENTION_PATTERN.sub("[USUARIO]", text)
    text = EMAIL_PATTERN.sub("[EMAIL]", text)
    text = PHONE_PATTERN.sub("[TELEFONO]", text)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def preprocess_dataframe(df: pd.DataFrame, text_column: str = "Texto_Original") -> pd.DataFrame:
    """Aplica preprocesamiento completo a un DataFrame."""
    result = df.copy()
    result["texto_limpio"] = result[text_column].map(normalize_text)
    result["texto_anonimizado"] = result[text_column].map(anonymize_text)
    result = result[result["texto_limpio"].str.len() > 0].reset_index(drop=True)
    return result
