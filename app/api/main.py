# -*- coding: utf-8 -*-
"""API FastAPI para XLM-R Large salvadoreño publicado en Hugging Face.

Usa la MISMA normalización del entrenamiento (src/features/normalization.py).
El modelo se descarga automáticamente desde Hugging Face en la primera inferencia.

    uvicorn app.api.main:app --port 8000
"""
import sys
from pathlib import Path

import torch
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MODELO_HF = "TheArbite/xlmr-large-hateval-hate-speech-sv"
REVISION_HF = "9476aae3116cf3a2bde95b9a410284c5186a1f1f"
MAX_LEN = 128

app = FastAPI(title="Toxicidad y discurso de odio — El Salvador", version="1.0.0")
_dev = "cuda" if torch.cuda.is_available() else "cpu"
_tok, _modelo = None, None


def _cargar():
    global _tok, _modelo
    if _modelo is not None:
        return
    tok = AutoTokenizer.from_pretrained(MODELO_HF, revision=REVISION_HF)
    modelo = AutoModelForSequenceClassification.from_pretrained(
        MODELO_HF, revision=REVISION_HF, low_cpu_mem_usage=True
    )
    etiquetas_cfg = modelo.config.id2label
    etiquetas = [etiquetas_cfg.get(i, etiquetas_cfg.get(str(i))) for i in range(len(CLASES))]
    etiquetas_genericas = [f"LABEL_{i}" for i in range(len(CLASES))]
    if modelo.config.num_labels != len(CLASES) or etiquetas not in (CLASES, etiquetas_genericas):
        raise RuntimeError(
            f"El modelo {MODELO_HF} no coincide con las clases esperadas: {etiquetas}"
        )
    # El repositorio publica LABEL_0..LABEL_3; se usa el orden canónico del proyecto.
    _tok = tok
    _modelo = modelo.to(_dev).eval()


class Entrada(BaseModel):
    texto: str = Field(min_length=1, max_length=5000)


@torch.no_grad()
def predecir(texto: str) -> dict:
    _cargar()
    enc = _tok(normalizar(texto), truncation=True, max_length=MAX_LEN, return_tensors="pt").to(_dev)
    q = torch.softmax(_modelo(**enc).logits, dim=-1).cpu().numpy()[0]
    k = int(q.argmax())
    return {"clase": CLASES[k], "label": k, "confianza": float(q[k]),
            "probabilidades": {c: float(v) for c, v in zip(CLASES, q)},
            "n_modelos": 1, "modelo": MODELO_HF}


@app.get("/salud")
def salud():
    return {"ok": True, "modelos_cargados": int(_modelo is not None),
            "modelo": MODELO_HF, "revision": REVISION_HF, "dispositivo": _dev}


@app.post("/predecir")
def post_predecir(e: Entrada):
    return predecir(e.texto)
