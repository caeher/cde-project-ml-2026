#!/usr/bin/env python
"""Fine-tuning ligero de mBERT y XLM-R."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.config import load_config
from discurso_odio.data.loader import load_dataset, prepare_dataset
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.models.transformers_ft import run_all_finetuning


def main() -> None:
    config = load_config()
    train_df = preprocess_dataframe(prepare_dataset(load_dataset("entrenamiento")))
    X = train_df["texto_limpio"]
    y = train_df["label"]

    print("Iniciando fine-tuning ligero (mBERT + XLM-R)...")
    results = run_all_finetuning(X, y)
    for model_key, result in results.items():
        print(f"{model_key}: métricas en {result['metrics_path']}")
        print(f"  eval: {result['eval_metrics']}")


if __name__ == "__main__":
    main()
