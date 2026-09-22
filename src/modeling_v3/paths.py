"""Rutas del repositorio para el motor V3."""

from pathlib import Path


def get_project_root() -> Path:
    """Raíz del proyecto (directorio con `config/` y `data/`)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "config").is_dir() and (parent / "data").is_dir():
            return parent
    raise FileNotFoundError("No se encontró la raíz del proyecto.")


def default_data_dir() -> Path:
    return get_project_root() / "data" / "processed" / "v3"


def default_models_dir() -> Path:
    path = get_project_root() / "models" / "v3"
    path.mkdir(parents=True, exist_ok=True)
    return path


def lexicon_salvadoreno_path() -> Path:
    return get_project_root() / "data" / "raw" / "lexicon_salvadoreno.csv"
