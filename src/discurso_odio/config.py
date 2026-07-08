"""Carga y gestión de configuración del proyecto."""

from pathlib import Path

import yaml

from discurso_odio.utils.paths import get_project_root


def load_config(config_name: str = "settings.yaml") -> dict:
    """Carga el archivo de configuración YAML desde config/."""
    config_path = get_project_root() / "config" / config_name
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
