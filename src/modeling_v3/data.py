"""Validación del contrato de datos V3 y reconstrucción (deshabilitada sin léxico)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from modeling_v3.constants import EXPECTED_ROWS, REFERENCE_SHA256, TEXT_COLUMN
from modeling_v3.paths import default_data_dir, lexicon_salvadoreno_path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def leer_csv(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    return d


def validar_contrato(data_dir: Path | None = None) -> dict:
    """
    Comprueba presencia, hashes y esquema mínimo de val/test.
    Devuelve un resumen serializable (para CLI y pruebas).
    """
    root = data_dir if data_dir is not None else default_data_dir()
    if not root.is_dir():
        raise FileNotFoundError(f"No existe el directorio de datos V3: {root}")

    resultado: dict = {"data_dir": str(root), "archivos": {}, "ok": True}
    requeridos = list(REFERENCE_SHA256.keys())

    for nombre in requeridos:
        ruta = root / nombre
        if not ruta.is_file():
            resultado["ok"] = False
            resultado["archivos"][nombre] = {"presente": False}
            continue
        sha = _sha256_file(ruta)
        esperado = REFERENCE_SHA256[nombre]
        coincide = sha == esperado
        if not coincide:
            resultado["ok"] = False
        resultado["archivos"][nombre] = {
            "presente": True,
            "sha256": sha,
            "sha256_esperado": esperado,
            "coincide": coincide,
        }

    for nombre, n_filas in EXPECTED_ROWS.items():
        ruta = root / nombre
        if not ruta.is_file():
            continue
        df = leer_csv(ruta)
        if TEXT_COLUMN not in df.columns or "label" not in df.columns:
            resultado["ok"] = False
            resultado.setdefault("esquema", {})[nombre] = "faltan columnas texto_modelo o label"
            continue
        if len(df) != n_filas:
            resultado["ok"] = False
        labels = set(df["label"].astype(int).unique())
        if labels - {0, 1, 2, 3}:
            resultado["ok"] = False
        resultado.setdefault("filas", {})[nombre] = {
            "n": len(df),
            "n_esperado": n_filas,
            "labels": sorted(labels),
        }

    meta = root / "metadata.json"
    if meta.is_file():
        resultado["metadata"] = json.loads(meta.read_text(encoding="utf-8"))

    return resultado


def reconstruir(_data_dir: Path | None = None) -> None:
    """
    Reconstrucción completa del train V3 (sintéticos + reales).
    Requiere lexicon_salvadoreno.csv; no forma parte del flujo por defecto.
    """
    lex = lexicon_salvadoreno_path()
    if not lex.is_file():
        raise FileNotFoundError(
            "La reconstrucción del dataset V3 requiere "
            f"{lex}, que no está versionado en este repositorio. "
            "Use los splits congelados en data/processed/v3/ y `build-data` "
            "solo para validar el contrato."
        )
    # Port futuro: augmentation_v3 + construir_dataset desde la rama v3.
    raise NotImplementedError(
        "reconstruir() no está habilitado en main hasta incorporar el léxico. "
        "Los CSV en data/processed/v3/ son la fuente de verdad."
    )
