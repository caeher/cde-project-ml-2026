#!/usr/bin/env python
"""Entrena y evalúa modelos baseline."""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.config import load_config
from discurso_odio.data.loader import load_dataset, prepare_dataset
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.models.baselines import get_baseline_models
from discurso_odio.models.evaluate import (
    compare_models,
    cross_validate_model,
    evaluate_model,
    plot_confusion_matrix,
    save_comparison_table,
    save_metrics_json,
)
from discurso_odio.data.taxonomy import CANONICAL_LABELS
from discurso_odio.models.train import save_model


def main() -> None:
    config = load_config()
    train_df = prepare_dataset(load_dataset("entrenamiento"))
    test_df = prepare_dataset(load_dataset("pruebas"))
    train_df = preprocess_dataframe(train_df)
    test_df = preprocess_dataframe(test_df)

    X_train = train_df["texto_limpio"]
    y_train = train_df["label"]
    X_test = test_df["texto_limpio"]
    y_test = test_df["label"]

    results = {}
    models = get_baseline_models(max_features=config["model"]["max_features"])
    for name, model in models.items():
        print(f"Entrenando {name}...")
        model.fit(X_train, y_train)
        cv = cross_validate_model(model, X_train, y_train, cv=config["model"]["cv_folds"])
        eval_result = evaluate_model(model, X_test, y_test)
        results[name] = {**eval_result, "cv": cv}
        save_model(model, name=name)
        plot_confusion_matrix(
            eval_result["confusion_matrix"],
            CANONICAL_LABELS,
            f"Matriz de confusión — {name}",
            f"07_confusion_{name}.png",
        )

    table = compare_models(results)
    table_path = save_comparison_table(table)
    metrics_path = save_metrics_json(
        {k: {"metrics": v["metrics"], "cv": v.get("cv")} for k, v in results.items()},
        "baseline_metrics.json",
    )
    print(table.to_string(index=False))
    print(f"Tabla comparativa: {table_path}")
    print(f"Métricas JSON: {metrics_path}")


if __name__ == "__main__":
    main()
