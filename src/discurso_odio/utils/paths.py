"""Utilidades para rutas del proyecto."""

from pathlib import Path


def get_project_root() -> Path:
    """Devuelve la raíz del proyecto (directorio que contiene config/ y data/)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "config").is_dir() and (parent / "data").is_dir():
            return parent
    raise FileNotFoundError("No se encontró la raíz del proyecto.")


def get_data_dir(subdir: str = "raw") -> Path:
    """Devuelve la ruta a un subdirectorio de data/."""
    path = get_project_root() / "data" / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_models_dir() -> Path:
    """Devuelve la ruta al directorio de modelos entrenados."""
    path = get_project_root() / "models" / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path
