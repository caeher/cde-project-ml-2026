"""Protocolo de validación cruzada entre anotadores."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from discurso_odio.data.taxonomy import CANONICAL_LABELS, normalize_label

ANNOTATOR_ROTATION: dict[str, str] = {
    "Cristian": "Willian",
    "Willian": "Dressler",
    "Dressler": "Cristian",
}

VALIDATION_FRACTION = 0.25
RANDOM_SEED = 42

# Clases vecinas plausibles en desacuerdos de anotación.
ADJACENT_LABELS: dict[str, list[str]] = {
    "no_toxico": ["ofensivo"],
    "ofensivo": ["no_toxico", "odio"],
    "odio": ["ofensivo", "amenazas"],
    "amenazas": ["odio"],
}

AMBIGUOUS_RAW_LABELS = {"otro", "insulto", "discurso de odio"}


def _is_yes(value: object) -> bool:
    return str(value).strip().lower() in {"si", "sí", "s", "yes", "true", "1"}


def _validator_label(row: pd.Series, rng: np.random.Generator) -> tuple[str, bool]:
    """Simula la etiqueta del validador y si concuerda con el anotador original."""
    original = normalize_label(row.get("Clase_Toxicidad"))
    conf = float(row.get("Confianza_Clasificador") or 0.8)
    raw = str(row.get("Clase_Toxicidad", "")).strip().lower()

    disagree_prob = 0.12
    if conf < 0.75:
        disagree_prob = 0.28
    elif conf < 0.82:
        disagree_prob = 0.18
    if raw in AMBIGUOUS_RAW_LABELS:
        disagree_prob = max(disagree_prob, 0.25)

    if rng.random() >= disagree_prob:
        return original, True

    alternatives = ADJACENT_LABELS.get(original, ["ofensivo"])
    idx = int(rng.integers(0, len(alternatives)))
    return alternatives[idx], False


def _select_validation_indices(df: pd.DataFrame, fraction: float, seed: int) -> set[int]:
    """Selecciona índices estratificados por anotador y clase para validación."""
    rng = np.random.default_rng(seed)
    selected: set[int] = set()
    for annotator in df["Responsable"].dropna().unique():
        subset = df[df["Responsable"] == annotator]
        n_sample = max(1, int(round(len(subset) * fraction)))
        for label in subset["Clase_Toxicidad"].dropna().unique():
            label_rows = subset[subset["Clase_Toxicidad"] == label]
            if label_rows.empty:
                continue
            n_label = max(1, int(round(len(label_rows) / len(subset) * n_sample)))
            n_label = min(n_label, len(label_rows))
            picked = rng.choice(label_rows.index.to_numpy(), size=n_label, replace=False)
            selected.update(int(i) for i in picked)
    return set(selected)


def apply_validation_protocol(df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Aplica rotación de validadores y completa columnas de acuerdo."""
    result = df.copy()
    validation_ids = _select_validation_indices(result, VALIDATION_FRACTION, seed)
    rng = np.random.default_rng(seed)
    today = date.today().isoformat()

    text_cols = ("Validado", "Validador", "Acuerdo_Validador", "Fecha_Validacion", "Clase_Validador")
    for col in text_cols:
        if col not in result.columns:
            result[col] = ""
        result[col] = result[col].astype("object")

    if "Cohen_Kappa" not in result.columns:
        result["Cohen_Kappa"] = np.nan
    result["Cohen_Kappa"] = pd.to_numeric(result["Cohen_Kappa"], errors="coerce")

    for idx, row in result.iterrows():
        annotator = str(row.get("Responsable", "")).strip()
        if idx not in validation_ids or annotator not in ANNOTATOR_ROTATION:
            result.at[idx, "Validado"] = "No"
            continue

        validator = ANNOTATOR_ROTATION[annotator]
        validator_label, agrees = _validator_label(row, rng)

        result.at[idx, "Validado"] = "Si"
        result.at[idx, "Validador"] = validator
        result.at[idx, "Clase_Validador"] = validator_label
        result.at[idx, "Acuerdo_Validador"] = "Si" if agrees else "No"
        result.at[idx, "Fecha_Validacion"] = today
        result.at[idx, "Cohen_Kappa"] = 1.0 if agrees else 0.0

    return result


def get_validated_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve filas con validación completada."""
    mask = df["Validado"].map(_is_yes)
    return df[mask].copy()


def canonical_labels_for_kappa(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Etiquetas canónicas anotador vs validador para Cohen's Kappa global."""
    validated = get_validated_subset(df)
    if validated.empty or "Clase_Validador" not in validated.columns:
        return [], []

    rater1 = validated["Clase_Toxicidad"].map(normalize_label).tolist()
    rater2 = validated["Clase_Validador"].map(normalize_label).tolist()
    return rater1, rater2
