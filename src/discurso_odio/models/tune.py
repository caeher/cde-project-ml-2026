"""Optimización de hiperparámetros para modelos baseline."""

from __future__ import annotations

from sklearn.model_selection import GridSearchCV

from discurso_odio.models.baselines import get_baseline_models


def tune_logistic_regression(X, y, cv: int = 3) -> GridSearchCV:
    """GridSearch para Regresión Logística."""
    pipeline = get_baseline_models()["logistic_regression"]
    param_grid = {
        "clf__C": [0.1, 1.0, 10.0],
        "tfidf__max_features": [5000, 10000],
    }
    search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X, y)
    return search


def tune_linear_svm(X, y, cv: int = 3) -> GridSearchCV:
    """GridSearch para LinearSVC."""
    pipeline = get_baseline_models()["linear_svm"]
    param_grid = {
        "clf__C": [0.1, 1.0, 10.0],
        "tfidf__max_features": [5000, 10000],
    }
    search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X, y)
    return search


def run_hyperparameter_tuning(X, y, cv: int = 3) -> dict:
    """Ejecuta optimización para los baselines principales."""
    lr_search = tune_logistic_regression(X, y, cv=cv)
    svm_search = tune_linear_svm(X, y, cv=cv)
    return {
        "logistic_regression": lr_search,
        "linear_svm": svm_search,
    }
