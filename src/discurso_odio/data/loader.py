"""Carga de datasets para el análisis de discurso de odio."""

from pathlib import Path

import pandas as pd

from discurso_odio.utils.paths import get_data_dir


def load_raw_dataset(filename: str) -> pd.DataFrame:
    """Carga un archivo CSV desde data/raw/."""
    path = get_data_dir("raw") / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {path}")
    return pd.read_csv(path)
