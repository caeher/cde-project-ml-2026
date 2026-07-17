#!/usr/bin/env python
"""Optimización de hiperparámetros (GridSearchCV)."""

import sys
from pathlib import Path

import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.config import load_config
from discurso_odio.data.loader import load_dataset, prepare_dataset
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.models.tune import run_hyperparameter_tuning
from discurso_odio.utils.paths import get_project_root


def main() -> None:
    config = load_config()
    train_df = preprocess_dataframe(prepare_dataset(load_dataset("entrenamiento")))
    X = train_df["texto_limpio"]
    y = train_df["label"]

    print("Iniciando optimización de hiperparámetros...")
    searches = run_hyperparameter_tuning(X, y, cv=3)
    report = {}
    for name, search in searches.items():
        report[name] = {
            "best_params": search.best_params_,
            "best_score": float(search.best_score_),
        }
        print(f"{name}: best F1={search.best_score_:.4f}, params={search.best_params_}")

    output = get_project_root() / "reports" / "hyperparameter_tuning.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Reporte guardado: {output}")


if __name__ == "__main__":
    main()
