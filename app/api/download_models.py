"""Descarga los pesos necesarios para una imagen o entorno de deploy.

Ejemplos:
    python -m app.api.download_models
    PRELOAD_MODELS=robertuito-v3-sv,mbert-sv python -m app.api.download_models
"""
from __future__ import annotations

from .model_catalog import download_model, selected_model_keys


def main() -> None:
    keys = selected_model_keys()
    if not keys:
        print("No se configuraron modelos para precargar.")
        return

    for key in keys:
        print(f"Descargando {key}…", flush=True)
        ruta = download_model(key)
        print(f"  listo: {ruta}", flush=True)


if __name__ == "__main__":
    main()
