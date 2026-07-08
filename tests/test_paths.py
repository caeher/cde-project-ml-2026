"""Pruebas de utilidades de rutas."""

from discurso_odio.utils.paths import get_data_dir, get_project_root


def test_get_project_root():
    root = get_project_root()
    assert (root / "config").is_dir()
    assert (root / "data").is_dir()


def test_get_data_dir():
    raw_dir = get_data_dir("raw")
    assert raw_dir.name == "raw"
    assert raw_dir.exists()
