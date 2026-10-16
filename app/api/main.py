# -*- coding: utf-8 -*-
"""API FastAPI: RoBERTuito único (v3.4.0, destilado de un ensamble de 6 modelos) + temperature scaling.

Usa la MISMA normalización del entrenamiento (src/features/normalization.py).
Sin reglas post-hoc: la clase es el argmax del ensemble calibrado.

    uvicorn app.api.main:app --port 8000
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MODELOS = RAIZ / "models" / "v3.4.0"   # carpeta con manifest.json (ensamble de varias carpetas de modelos) o carpeta con semilla_*/modelo
_man = MODELOS / "manifest.json"
TEMPERATURA = json.loads(_man.read_text(encoding="utf-8"))["temperatura"] if _man.exists() else 1.619  # ajustada solo en val
MAX_LEN = 128

app = FastAPI(title="Toxicidad y discurso de odio — El Salvador", version="3.4.0")
_dev = "cuda" if torch.cuda.is_available() else "cpu"
_tok, _modelos = None, []


def _cargar():
    global _tok, _modelos
    if _modelos:
        return
    man = MODELOS / "manifest.json"
    if man.exists():
        cfg = json.loads(man.read_text(encoding="utf-8"))
        dirs = sorted(p for c in cfg["componentes"] for p in (MODELOS.parent / c).glob("semilla_*/modelo") if p.is_dir())
        global TEMPERATURA
        TEMPERATURA = cfg["temperatura"]
    else:
        dirs = sorted(p for p in MODELOS.glob("semilla_*/modelo") if p.is_dir())
    if not dirs:
        raise RuntimeError(f"no hay modelos en {MODELOS}; entrenar con --guardar_modelos")
    _tok = AutoTokenizer.from_pretrained(dirs[0])
    _modelos = [AutoModelForSequenceClassification.from_pretrained(d).to(_dev).eval() for d in dirs]


class Entrada(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)


@torch.no_grad()
def predecir(texto: str) -> dict:
    _cargar()
    enc = _tok(normalizar(texto), truncation=True, max_length=MAX_LEN, return_tensors="pt").to(_dev)
    p = np.mean([torch.softmax(m(**enc).logits.double(), -1).cpu().numpy()[0] for m in _modelos], 0)
    z = np.log(np.clip(p, 1e-12, 1)) / TEMPERATURA
    q = np.exp(z - z.max()); q /= q.sum()
    k = int(q.argmax())
    return {"clase": CLASES[k], "label": k, "confianza": float(q[k]),
            "probabilidades": {c: float(v) for c, v in zip(CLASES, q)}, "n_modelos": len(_modelos)}


@app.get("/salud")
def salud():
    return {"ok": True, "modelos_cargados": len(_modelos), "dispositivo": _dev}


@app.post("/predecir")
def post_predecir(e: Entrada):
    return predecir(e.texto)
