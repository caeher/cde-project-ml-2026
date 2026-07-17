"""Modelos baseline para clasificación de discurso de odio."""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from discurso_odio.models.train import build_baseline_pipeline


def build_logistic_regression(max_features: int = 10000) -> Pipeline:
    """TF-IDF + Regresión Logística."""
    return build_baseline_pipeline(max_features=max_features)


def build_linear_svm(max_features: int = 10000) -> Pipeline:
    """TF-IDF + LinearSVC."""
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))),
            ("clf", LinearSVC(random_state=42)),
        ]
    )


def build_multinomial_nb(max_features: int = 10000) -> Pipeline:
    """TF-IDF + Naive Bayes Multinomial."""
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))),
            ("clf", MultinomialNB()),
        ]
    )


def get_baseline_models(max_features: int = 10000) -> dict[str, Pipeline]:
    """Devuelve al menos 3 modelos baseline listos para entrenar."""
    return {
        "logistic_regression": build_logistic_regression(max_features),
        "linear_svm": build_linear_svm(max_features),
        "multinomial_nb": build_multinomial_nb(max_features),
    }
