#!/usr/bin/env python
"""Interpretabilidad SHAP/LIME sobre el mejor baseline."""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.data.loader import load_dataset, prepare_dataset
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.models.interpret import run_interpretability
from discurso_odio.utils.paths import get_models_dir


def main() -> None:
    test_df = preprocess_dataframe(prepare_dataset(load_dataset("pruebas")))
    model_path = get_models_dir() / "logistic_regression.joblib"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en {model_path}. Ejecuta scripts/run_baselines.py primero."
        )
    pipeline = joblib.load(model_path)
    sample_texts = test_df["texto_limpio"].head(20).tolist()
    result = run_interpretability(pipeline, sample_texts)
    print(f"SHAP: {result['shap_figure']}")
    print(f"LIME top label: {result['lime']['top_label']}")
    print(f"LIME features: {result['lime']['features'][:5]}")


if __name__ == "__main__":
    main()
