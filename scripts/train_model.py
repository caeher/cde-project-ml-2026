#!/usr/bin/env python
"""Script de ejemplo para entrenar un modelo baseline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.config import load_config
from discurso_odio.models.train import build_baseline_pipeline, save_model


def main() -> None:
    config = load_config()
    pipeline = build_baseline_pipeline(
        max_features=config["model"]["max_features"],
    )
    print(f"Pipeline baseline listo: {pipeline}")
    print("Carga datos con discurso_odio.data.loader y llama a pipeline.fit(X, y).")
    # Ejemplo: save_model(pipeline.fit(X_train, y_train))


if __name__ == "__main__":
    main()
