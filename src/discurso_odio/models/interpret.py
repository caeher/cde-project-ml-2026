"""Interpretabilidad de modelos (SHAP y LIME)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import shap
from lime.lime_text import LimeTextExplainer
from sklearn.pipeline import Pipeline

from discurso_odio.data.taxonomy import CANONICAL_LABELS
from discurso_odio.utils.paths import get_project_root


def _get_vectorizer_and_classifier(pipeline: Pipeline):
    """Extrae vectorizador y clasificador de un pipeline sklearn."""
    vectorizer = pipeline.named_steps.get("tfidf") or pipeline.named_steps.get("vect")
    classifier = pipeline.named_steps.get("clf")
    return vectorizer, classifier


def explain_with_shap(
    pipeline: Pipeline,
    X_sample: list[str],
    max_features: int = 15,
) -> Path:
    """Genera explicación SHAP para el mejor baseline."""
    vectorizer, classifier = _get_vectorizer_and_classifier(pipeline)
    X_vec = vectorizer.transform(X_sample[:20])

    fig_dir = get_project_root() / "reports" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    output = fig_dir / "06_shap_summary.png"

    plt.figure(figsize=(10, 6))
    if hasattr(classifier, "coef_"):
        # Regresión logística / LinearSVC: usar valores SHAP lineales
        if hasattr(classifier, "predict_proba"):
            explainer = shap.LinearExplainer(classifier, X_vec)
            shap_values = explainer.shap_values(X_vec)
        else:
            explainer = shap.LinearExplainer(classifier, X_vec)
            shap_values = explainer.shap_values(X_vec)

        feature_names = vectorizer.get_feature_names_out()
        if isinstance(shap_values, list):
            # Multiclase: usar la clase con mayor importancia media
            mean_abs = [np.abs(sv).mean() for sv in shap_values]
            best_class = int(np.argmax(mean_abs))
            shap.summary_plot(
                shap_values[best_class],
                X_vec,
                feature_names=feature_names,
                show=False,
                max_display=max_features,
            )
        else:
            shap.summary_plot(
                shap_values,
                X_vec,
                feature_names=feature_names,
                show=False,
                max_display=max_features,
            )
    else:
        # Fallback: importancia de coeficientes promedio
        plt.text(0.5, 0.5, "SHAP no disponible para este clasificador", ha="center")

    plt.tight_layout()
    plt.savefig(output, dpi=120, bbox_inches="tight")
    plt.close()
    return output


def explain_with_lime(
    pipeline: Pipeline,
    text: str,
    num_features: int = 10,
) -> dict:
    """Genera explicación LIME para un texto individual."""
    vectorizer, classifier = _get_vectorizer_and_classifier(pipeline)

    def predict_proba(texts):
        X_vec = vectorizer.transform(texts)
        if hasattr(classifier, "predict_proba"):
            return classifier.predict_proba(X_vec)
        scores = classifier.decision_function(X_vec)
        if scores.ndim == 1:
            scores = np.column_stack([-scores, scores])
        exp = np.exp(scores - scores.max(axis=1, keepdims=True))
        return exp / exp.sum(axis=1, keepdims=True)

    explainer = LimeTextExplainer(class_names=CANONICAL_LABELS)
    explanation = explainer.explain_instance(
        text,
        predict_proba,
        num_features=num_features,
        top_labels=len(CANONICAL_LABELS),
    )

    top_label_idx = (
        explanation.top_labels[0]
        if hasattr(explanation, "top_labels") and explanation.top_labels
        else (explanation.top_label if hasattr(explanation, "top_label") else 0)
    )
    result = {
        "text": text,
        "top_label": CANONICAL_LABELS[top_label_idx] if top_label_idx is not None else None,
        "features": explanation.as_list(label=top_label_idx),
    }

    output = get_project_root() / "reports" / "lime_explanation.json"
    with output.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return result


def run_interpretability(
    pipeline: Pipeline,
    X_sample: list[str],
) -> dict:
    """Ejecuta SHAP y LIME sobre muestra de textos."""
    shap_path = explain_with_shap(pipeline, X_sample[:20])
    lime_result = explain_with_lime(pipeline, X_sample[0])
    return {"shap_figure": str(shap_path), "lime": lime_result}
