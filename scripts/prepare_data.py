#!/usr/bin/env python
"""Script de ejemplo para preparar datos crudos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.config import load_config
from discurso_odio.utils.paths import get_data_dir


def main() -> None:
    config = load_config()
    raw_dir = get_data_dir("raw")
    print(f"Proyecto: {config['project']['name']}")
    print(f"Directorio de datos crudos: {raw_dir}")
    print("Coloca tus datasets en data/raw/ y ejecuta el pipeline de preprocesamiento.")


if __name__ == "__main__":
    main()
