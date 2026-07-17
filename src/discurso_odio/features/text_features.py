"""Feature engineering a partir de metadatos del corpus."""

from __future__ import annotations

import re

import pandas as pd

YES_VALUES = {"si", "sí", "s", "yes", "true", "1"}


def _to_bool(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in YES_VALUES


def extract_text_features(df: pd.DataFrame, text_column: str = "texto_limpio") -> pd.DataFrame:
    """Genera features numéricas y binarias a partir del texto y metadatos."""
    features = pd.DataFrame(index=df.index)
    text = df[text_column].fillna("").astype(str)

    features["char_len"] = text.str.len()
    features["word_count"] = text.str.split().str.len()
    features["upper_ratio"] = text.apply(
        lambda t: sum(1 for c in t if c.isupper()) / max(len(t), 1)
    )
    features["exclamation_count"] = text.str.count("!")
    features["question_count"] = text.str.count(r"\?")
    features["has_url"] = text.str.contains(r"http|www\.", regex=True).astype(int)

    if "Presencia_Sarcasmo" in df.columns:
        features["sarcasmo"] = df["Presencia_Sarcasmo"].map(_to_bool).astype(int)
    if "Presencia_Ironia" in df.columns:
        features["ironia"] = df["Presencia_Ironia"].map(_to_bool).astype(int)
    if "Contexto_Politico" in df.columns:
        features["contexto_politico"] = df["Contexto_Politico"].map(_to_bool).astype(int)
    if "Plataforma" in df.columns:
        features["es_x"] = (
            df["Plataforma"].astype(str).str.lower().str.contains("x|twitter").astype(int)
        )
    if "Lenguaje_Dialectal" in df.columns:
        dialect = df["Lenguaje_Dialectal"].astype(str).str.lower()
        features["dialecto_salvadoreno"] = dialect.str.contains("salvad").astype(int)

    return features


def combine_text_and_metadata(
    texts: pd.Series,
    metadata_features: pd.DataFrame,
    separator: str = " [SEP] ",
) -> pd.Series:
    """Combina texto con resumen de metadatos para modelos que aceptan texto enriquecido."""
    meta_strings = metadata_features.apply(
        lambda row: " ".join(
            f"{col}={int(row[col])}" for col in metadata_features.columns if row[col] != 0
        ),
        axis=1,
    )
    return texts.fillna("").astype(str) + separator + meta_strings
