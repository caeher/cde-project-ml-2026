# -*- coding: utf-8 -*-
"""API FastAPI: varios backends (RoBERTuito v3.4.0 / v3.6.0, XLM-R HF o local).

Usa la MISMA normalización del entrenamiento (src/features/normalization.py).

    uvicorn app.api.main:app --port 8000

Variable de entorno opcional: API_MODELO_DEFAULT (p. ej. v3.6.0, xlmr_hf).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar  # noqa: E402
from src.models.xlmr import CLASES, XLMR_HF_ID, XLMR_HF_REVISION, cargar_xlmr, resolver_local

MAX_LEN = 128

CATALOGO: list[dict[str, str]] = [
    {
        "id": "v3.6.0",
        "etiqueta": "RoBERTuito v3.6.0",
        "descripcion": "Destilado sobre dataset v2.0.0 (requiere carpeta models/v3.6.0/)",
    },
    {
        "id": "v3.4.0",
        "etiqueta": "RoBERTuito v3.4.0",
        "descripcion": "Modelo único sobre dataset v1.8.0 (requiere models/v3.4.0/)",
    },
    {
        "id": "xlmr_hf",
        "etiqueta": "XLM-R Large (Hugging Face)",
        "descripcion": XLMR_HF_ID,
    },
    {
        "id": "xlmr_local",
        "etiqueta": "XLM-R (local)",
        "descripcion": "Pesos en models/xlmr_hate_speech_sv/ (notebook notebooks/train/xlmr_hateval/)",
    },
]

MODELO_DEFAULT = os.environ.get("API_MODELO_DEFAULT", "v3.6.0")

app = FastAPI(title="Toxicidad y discurso de odio — El Salvador", version="3.6.0-multi")
_dev = "cuda" if torch.cuda.is_available() else "cpu"
_cache: dict[str, dict[str, Any]] = {}


def _resolver_raiz(version: str) -> Path:
    return RAIZ / "models" / version


def _dirs_robertuito(base: Path) -> tuple[list[Path], float]:
    man = base / "manifest.json"
    temperatura = 1.619
    if man.exists():
        cfg = json.loads(man.read_text(encoding="utf-8"))
        temperatura = float(cfg["temperatura"])
        dirs = sorted(
            p
            for c in cfg["componentes"]
            for p in (base.parent / c).glob("semilla_*/modelo")
            if p.is_dir()
        )
    else:
        dirs = sorted(p for p in base.glob("semilla_*/modelo") if p.is_dir())
        if not dirs and (base / "manifest.json").parent == base:
            pass
    if not dirs:
        dirs = sorted(p for p in base.glob("semilla_*/modelo") if p.is_dir())
    if not dirs:
        raise RuntimeError(f"no hay modelos en {base}; entrenar o copiar pesos locales")
    return dirs, temperatura


def _cargar_robertuito(modelo_id: str, version: str) -> dict[str, Any]:
    base = _resolver_raiz(version)
    dirs, temperatura = _dirs_robertuito(base)
    tok = AutoTokenizer.from_pretrained(dirs[0])
    modelos = [
        AutoModelForSequenceClassification.from_pretrained(d).to(_dev).eval() for d in dirs
    ]
    return {
        "tipo": "ensemble",
        "id": modelo_id,
        "nombre": CATALOGO[next(i for i, c in enumerate(CATALOGO) if c["id"] == modelo_id)]["etiqueta"],
        "tok": tok,
        "modelos": modelos,
        "temperatura": temperatura,
    }


def _estado_xlmr(*, solo_remoto: bool = False) -> dict[str, Any]:
    tok, modelo, _, local = cargar_xlmr(solo_remoto=solo_remoto)
    return {
        "tipo": "hf",
        "id": "xlmr_local" if local is not None else "xlmr_hf",
        "nombre": str(local) if local is not None else XLMR_HF_ID,
        "tok": tok,
        "modelo": modelo,
        "revision": None if local is not None else XLMR_HF_REVISION,
    }


def _cargar_xlmr_hf() -> dict[str, Any]:
    return _estado_xlmr(solo_remoto=True)


def _cargar_xlmr_local() -> dict[str, Any]:
    return _estado_xlmr()


def _obtener(modelo_id: str) -> dict[str, Any]:
    if modelo_id in _cache:
        return _cache[modelo_id]
    if modelo_id == "v3.6.0":
        st = _cargar_robertuito(modelo_id, "v3.6.0")
    elif modelo_id == "v3.4.0":
        st = _cargar_robertuito(modelo_id, "v3.4.0")
    elif modelo_id == "xlmr_hf":
        st = _cargar_xlmr_hf()
    elif modelo_id == "xlmr_local":
        st = _cargar_xlmr_local()
    else:
        raise ValueError(f"modelo_id desconocido: {modelo_id}")
    _cache[modelo_id] = st
    return st


class Entrada(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)
    modelo_id: Optional[str] = Field(default=None, description="Clave del catálogo /modelos")


@torch.no_grad()
def _predecir_con_estado(st: dict[str, Any], texto: str) -> dict[str, Any]:
    norm = normalizar(texto)
    enc = st["tok"](norm, truncation=True, max_length=MAX_LEN, return_tensors="pt").to(_dev)
    if st["tipo"] == "ensemble":
        p = np.mean(
            [torch.softmax(m(**enc).logits.double(), -1).cpu().numpy()[0] for m in st["modelos"]],
            0,
        )
        z = np.log(np.clip(p, 1e-12, 1)) / st["temperatura"]
        q = np.exp(z - z.max())
        q /= q.sum()
        n_modelos = len(st["modelos"])
    else:
        q = torch.softmax(st["modelo"](**enc).logits, dim=-1).cpu().numpy()[0]
        n_modelos = 1
    k = int(q.argmax())
    return {
        "clase": CLASES[k],
        "label": k,
        "confianza": float(q[k]),
        "probabilidades": {c: float(v) for c, v in zip(CLASES, q)},
        "n_modelos": n_modelos,
        "modelo_id": st["id"],
        "modelo": st["nombre"],
    }


def predecir(texto: str, modelo_id: Optional[str] = None) -> dict[str, Any]:
    mid = modelo_id or MODELO_DEFAULT
    st = _obtener(mid)
    return _predecir_con_estado(st, texto)


@app.get("/modelos")
def listar_modelos():
    items = []
    for meta in CATALOGO:
        items.append(
            {
                **meta,
                "cargado": meta["id"] in _cache,
                "disponible_local": _disponible_local(meta["id"]),
            }
        )
    return {"default": MODELO_DEFAULT, "modelos": items, "dispositivo": _dev}


def _disponible_local(modelo_id: str) -> bool:
    if modelo_id in ("v3.6.0", "v3.4.0"):
        try:
            _dirs_robertuito(_resolver_raiz(modelo_id))
            return True
        except RuntimeError:
            return False
    if modelo_id == "xlmr_hf":
        return True
    if modelo_id == "xlmr_local":
        return resolver_local() is not None
    return False


# Preserve explicit selections; a clean checkout has no RoBERTuito weights.
if "API_MODELO_DEFAULT" not in os.environ and not _disponible_local(MODELO_DEFAULT):
    MODELO_DEFAULT = "xlmr_local" if _disponible_local("xlmr_local") else "xlmr_hf"


@app.get("/salud")
def salud(modelo_id: Optional[str] = Query(None)):
    mid = modelo_id or MODELO_DEFAULT
    payload: dict[str, Any] = {
        "ok": True,
        "modelo_id": mid,
        "modelo_default": MODELO_DEFAULT,
        "dispositivo": _dev,
    }
    try:
        st = _obtener(mid)
        payload["modelo"] = st["nombre"]
        payload["modelos_cargados"] = len(st["modelos"]) if st["tipo"] == "ensemble" else 1
        if st.get("revision"):
            payload["revision"] = st["revision"]
    except Exception as exc:
        payload["ok"] = False
        payload["error"] = str(exc)
    # Compatibilidad con UI antigua que lee top-level "modelo"
    if payload.get("ok") and "modelo" not in payload:
        payload["modelo"] = mid
    return payload


@app.post("/predecir")
def post_predecir(e: Entrada):
    return predecir(e.texto, e.modelo_id)
