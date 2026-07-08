"""Entrenamiento de modelos baseline para clasificación de odio."""

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from discurso_odio.utils.paths import get_models_dir


def build_baseline_pipeline(max_features: int = 10000) -> Pipeline:
    """Construye un pipeline TF-IDF + Regresión Logística."""
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )


def save_model(model: Pipeline, name: str = "baseline") -> Path:
    """Guarda el modelo entrenado en models/checkpoints/."""
    output = get_models_dir() / f"{name}.joblib"
    joblib.dump(model, output)
    return output
