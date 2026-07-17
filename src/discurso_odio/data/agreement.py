"""Utilidades para análisis de acuerdo inter-anotadores (Cohen's Kappa)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from discurso_odio.utils.paths import get_project_root


def extract_kappa_from_dataset(df: pd.DataFrame) -> dict:
    """Extrae estadísticas de Cohen's Kappa del dataset si están disponibles."""
    result = {"available": False, "mean": None, "count": 0, "values": []}
    if "Cohen_Kappa" not in df.columns:
        return result

    kappa_series = pd.to_numeric(df["Cohen_Kappa"], errors="coerce").dropna()
    if len(kappa_series) == 0:
        return result

    result["available"] = True
    result["mean"] = float(kappa_series.mean())
    result["count"] = int(len(kappa_series))
    result["values"] = kappa_series.tolist()
    return result


def compute_kappa(rater1: list, rater2: list) -> float:
    """Calcula Cohen's Kappa entre dos anotadores."""
    return float(cohen_kappa_score(rater1, rater2))


def save_kappa_report(df: pd.DataFrame, filename: str = "kappa_report.json") -> Path:
    """Guarda reporte de acuerdo inter-anotadores."""
    report = extract_kappa_from_dataset(df)
    if "Validado" in df.columns:
        report["validated_count"] = int(
            df["Validado"].astype(str).str.lower().isin({"si", "sí", "yes", "s"}).sum()
        )
    if "Acuerdo_Validador" in df.columns:
        agreement = df["Acuerdo_Validador"].astype(str).str.lower()
        report["agreement_rate"] = float(
            agreement.isin({"si", "sí", "yes", "s"}).mean()
        )

    output = get_project_root() / "reports" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return output
