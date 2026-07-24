"""Estadísticas del corpus para reportes."""

from __future__ import annotations

import pandas as pd

from discurso_odio.data.loader import (
    CANONICAL_LABEL_COLUMN,
    DATASET_FILES,
    TEXT_COLUMN,
    label_distribution,
    load_dataset,
    prepare_dataset,
)
from discurso_odio.data.taxonomy import CANONICAL_LABELS
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.features.text_features import extract_text_features

YES_VALUES = {"si", "sí", "s", "yes", "true", "1"}


def _yes_ratio(series: pd.Series) -> float:
    return float(series.astype(str).str.lower().isin(YES_VALUES).mean())


def get_dataset_summary() -> dict:
    """Genera estadísticas consolidadas del corpus para el reporte."""
    unificado = prepare_dataset(load_dataset("unificado"))
    train = prepare_dataset(load_dataset("entrenamiento"))
    test = prepare_dataset(load_dataset("pruebas"))

    labels = label_distribution(unificado)
    max_class = int(labels.max())
    min_class = int(labels[labels > 0].min()) if (labels > 0).any() else 0
    imbalance_ratio = round(max_class / max(min_class, 1), 1)

    processed = preprocess_dataframe(unificado)
    word_lens = processed["texto_limpio"].astype(str).str.split().map(len)
    p99_words = int(word_lens.quantile(0.99))

    train_texts = set(train[TEXT_COLUMN].astype(str).str.strip().str.lower())
    test_texts = set(test[TEXT_COLUMN].astype(str).str.strip().str.lower())
    leaks = len(train_texts & test_texts)

    platform = (
        unificado["Plataforma"].value_counts().to_dict() if "Plataforma" in unificado.columns else {}
    )

    dialect_pct = 0.0
    if "Lenguaje_Dialectal" in unificado.columns:
        dialect = unificado["Lenguaje_Dialectal"].astype(str).str.lower()
        dialect_pct = round(float(dialect.str.contains("salvad").mean()) * 100, 1)

    features = extract_text_features(processed)
    class_weights = {}
    total = len(unificado)
    for label in CANONICAL_LABELS:
        count = int(labels.get(label, 0))
        class_weights[label] = round(total / (len(CANONICAL_LABELS) * max(count, 1)), 2)

    amenazas_x = 0
    amenazas_fb = 0
    if "Plataforma" in unificado.columns:
        amen = unificado[unificado[CANONICAL_LABEL_COLUMN] == "amenazas"]
        amenazas_x = int((amen["Plataforma"].astype(str).str.upper() == "X").sum())
        amenazas_fb = int((amen["Plataforma"].astype(str).str.lower() == "facebook").sum())

    return {
        "total_unificado": len(unificado),
        "total_train": len(train),
        "total_test": len(test),
        "num_columns": len(unificado.columns),
        "label_counts": {k: int(v) for k, v in labels.items()},
        "label_pcts": {k: round(100 * v / total, 1) for k, v in labels.items()},
        "imbalance_ratio": imbalance_ratio,
        "platform": platform,
        "dialect_pct": dialect_pct,
        "sarcasm_pct": round(_yes_ratio(unificado["Presencia_Sarcasmo"]) * 100, 1)
        if "Presencia_Sarcasmo" in unificado.columns
        else 0.0,
        "irony_pct": round(_yes_ratio(unificado["Presencia_Ironia"]) * 100, 1)
        if "Presencia_Ironia" in unificado.columns
        else 0.0,
        "political_pct": round(_yes_ratio(unificado["Contexto_Politico"]) * 100, 1)
        if "Contexto_Politico" in unificado.columns
        else 0.0,
        "p99_words": p99_words,
        "mean_words": round(float(word_lens.mean()), 1),
        "train_test_leaks": leaks,
        "amenazas_x": amenazas_x,
        "amenazas_fb": amenazas_fb,
        "class_weights": class_weights,
        "mojibake_estimate": int(
            unificado[TEXT_COLUMN].astype(str).str.contains("\ufffd", regex=False).sum()
        ),
    }
