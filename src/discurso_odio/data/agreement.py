"""Utilidades para análisis de acuerdo inter-anotadores (Cohen's Kappa)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from discurso_odio.data.validation import canonical_labels_for_kappa, get_validated_subset
from discurso_odio.utils.paths import get_project_root


def _landis_koch_interpretation(kappa: float) -> str:
    if kappa < 0:
        return "pobre"
    if kappa < 0.20:
        return "ligero"
    if kappa < 0.40:
        return "razonable"
    if kappa < 0.60:
        return "moderado"
    if kappa < 0.80:
        return "sustancial"
    return "casi perfecto"


def extract_kappa_from_dataset(df: pd.DataFrame) -> dict:
    """Extrae estadísticas de Cohen's Kappa del dataset si están disponibles."""
    result: dict = {
        "available": False,
        "mean": None,
        "count": 0,
        "values": [],
        "global_kappa": None,
        "interpretation": None,
        "validated_count": 0,
        "agreement_rate": 0.0,
        "validation_fraction": 0.0,
    }

    validated = get_validated_subset(df)
    result["validated_count"] = int(len(validated))
    result["validation_fraction"] = float(len(validated) / max(len(df), 1))

    if validated.empty:
        return result

    if "Acuerdo_Validador" in validated.columns:
        agreement = validated["Acuerdo_Validador"].astype(str).str.lower()
        result["agreement_rate"] = float(
            agreement.isin({"si", "sí", "yes", "s"}).mean()
        )

    rater1, rater2 = canonical_labels_for_kappa(df)
    if rater1 and rater2:
        global_kappa = float(cohen_kappa_score(rater1, rater2))
        result["available"] = True
        result["global_kappa"] = global_kappa
        result["mean"] = global_kappa
        result["count"] = len(rater1)
        result["interpretation"] = _landis_koch_interpretation(global_kappa)

    if "Cohen_Kappa" in df.columns:
        kappa_series = pd.to_numeric(validated["Cohen_Kappa"], errors="coerce").dropna()
        if len(kappa_series) > 0:
            result["values"] = kappa_series.tolist()

    return result


def compute_kappa(rater1: list, rater2: list) -> float:
    """Calcula Cohen's Kappa entre dos anotadores."""
    return float(cohen_kappa_score(rater1, rater2))


def save_kappa_report(df: pd.DataFrame, filename: str = "kappa_report.json") -> Path:
    """Guarda reporte de acuerdo inter-anotadores."""
    report = extract_kappa_from_dataset(df)

    output = get_project_root() / "reports" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return output
