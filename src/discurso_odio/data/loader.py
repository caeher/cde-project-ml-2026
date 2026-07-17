"""Carga de datasets para el análisis de discurso de odio."""

from __future__ import annotations

from pathlib import Path

import ftfy
import pandas as pd

from discurso_odio.data.taxonomy import CANONICAL_LABELS, normalize_label
from discurso_odio.utils.paths import get_data_dir

DATASET_FILES = {
    "unificado": "dataset_unificado.csv",
    "entrenamiento": "dataset_entrenamiento.csv",
    "pruebas": "dataset_pruebas.csv",
}

TEXT_COLUMN = "Texto_Original"
LABEL_COLUMN = "Clase_Toxicidad"
CANONICAL_LABEL_COLUMN = "label"


def _fix_text(value: object) -> str:
    """Corrige mojibake y normaliza espacios en texto."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = ftfy.fix_text(str(value))
    return text.strip()


def _read_csv(path: Path) -> pd.DataFrame:
    """Lee CSV probando codificaciones comunes."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")


def load_raw_dataset(filename: str) -> pd.DataFrame:
    """Carga un archivo CSV desde data/raw/."""
    path = get_data_dir("raw") / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {path}")
    return _read_csv(path)


def load_dataset(split: str = "unificado") -> pd.DataFrame:
    """Carga un split del proyecto (unificado, entrenamiento, pruebas)."""
    if split not in DATASET_FILES:
        raise ValueError(f"Split desconocido: {split}. Opciones: {list(DATASET_FILES)}")
    return load_raw_dataset(DATASET_FILES[split])


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia texto, normaliza etiquetas y filtra filas inválidas."""
    result = df.copy()
    if TEXT_COLUMN not in result.columns:
        raise ValueError(f"Columna requerida ausente: {TEXT_COLUMN}")

    result[TEXT_COLUMN] = result[TEXT_COLUMN].map(_fix_text)
    result = result[result[TEXT_COLUMN].str.len() > 0].copy()

    if LABEL_COLUMN in result.columns:
        result[CANONICAL_LABEL_COLUMN] = result[LABEL_COLUMN].map(normalize_label)
    else:
        result[CANONICAL_LABEL_COLUMN] = "no_toxico"

    # Corregir columnas de texto adicionales
    for col in result.select_dtypes(include="object").columns:
        result[col] = result[col].map(lambda v: _fix_text(v) if isinstance(v, str) else v)

    return result.reset_index(drop=True)


def get_xy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Devuelve X (texto) e y (etiqueta canónica)."""
    prepared = prepare_dataset(df)
    return prepared[TEXT_COLUMN], prepared[CANONICAL_LABEL_COLUMN]


def label_distribution(df: pd.DataFrame) -> pd.Series:
    """Distribución de clases canónicas."""
    prepared = prepare_dataset(df)
    return prepared[CANONICAL_LABEL_COLUMN].value_counts().reindex(CANONICAL_LABELS, fill_value=0)
