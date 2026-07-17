"""Evaluación de modelos de clasificación."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score

from discurso_odio.data.taxonomy import CANONICAL_LABELS
from discurso_odio.utils.paths import get_project_root


def compute_metrics(y_true, y_pred) -> dict[str, float]:
    """Calcula métricas principales de clasificación."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_macro": float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def cross_validate_model(model, X, y, cv: int = 5) -> dict[str, float]:
    """Validación cruzada con F1 macro."""
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro", n_jobs=-1)
    return {
        "cv_f1_macro_mean": float(scores.mean()),
        "cv_f1_macro_std": float(scores.std()),
    }


def evaluate_model(model, X_test, y_test) -> dict:
    """Evalúa un modelo entrenado en conjunto de prueba."""
    y_pred = model.predict(X_test)
    metrics = compute_metrics(y_test, y_pred)
    report = classification_report(
        y_test, y_pred, labels=CANONICAL_LABELS, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_test, y_pred, labels=CANONICAL_LABELS)
    return {
        "metrics": metrics,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "y_pred": y_pred,
    }


def compare_models(results: dict[str, dict]) -> pd.DataFrame:
    """Tabla comparativa de métricas entre modelos."""
    rows = []
    for name, result in results.items():
        row = {"modelo": name, **result["metrics"]}
        if "cv" in result:
            row.update(result["cv"])
        rows.append(row)
    return pd.DataFrame(rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)


def save_comparison_table(df: pd.DataFrame, filename: str = "metricas_comparativas.csv") -> Path:
    """Guarda tabla comparativa en reports/."""
    output_dir = get_project_root() / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / filename
    df.to_csv(output, index=False)
    return output


def save_metrics_json(metrics: dict, filename: str) -> Path:
    """Guarda métricas en JSON."""
    output_dir = get_project_root() / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / filename
    with output.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    return output


def plot_confusion_matrix(cm, labels: list[str], title: str, filename: str) -> Path:
    """Genera y guarda matriz de confusión."""
    fig_dir = get_project_root() / "reports" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.xlabel("Predicción")
    plt.ylabel("Real")
    output = fig_dir / filename
    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()
    return output
