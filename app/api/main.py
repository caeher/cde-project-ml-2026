# -*- coding: utf-8 -*-
"""
API de clasificación de toxicidad — prototipo V3.

Regla de oro del proyecto: el endpoint aplica EXACTAMENTE el mismo normalizador
que se usó para entrenar. Si difieren, hay train/serve skew y las métricas del
informe dejan de describir lo que ocurre en producción. Por eso importa
`normalizar` del módulo único en lugar de reimplementarlo aquí.
"""
from __future__ import annotations

import json
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

MODELO = Path(__file__).resolve().parent.parent.parent / "models/v3/final"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MAX_LEN = 128
LOTE_MAXIMO = 64

_estado: dict = {}


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    if not MODELO.exists():
        raise RuntimeError(
            f"No hay modelo en {MODELO}. Ejecutá primero el entrenamiento de la V3.")
    _estado["tok"] = AutoTokenizer.from_pretrained(str(MODELO))
    _estado["mod"] = AutoModelForSequenceClassification.from_pretrained(str(MODELO)).eval()
    _estado["dev"] = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _estado["mod"].to(_estado["dev"])
    contrato = MODELO / "inference_contract.json"
    _estado["contrato"] = json.loads(contrato.read_text()) if contrato.exists() else {}
    yield
    _estado.clear()


app = FastAPI(
    title="Detección de toxicidad — corpus salvadoreño",
    description="Clasificación en cuatro niveles de gravedad para publicaciones "
                "de X y Facebook en registro salvadoreño.",
    version="3.0", lifespan=ciclo_de_vida)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class Peticion(BaseModel):
    texto: str = Field(..., min_length=1, max_length=4000,
                       json_schema_extra={"example": "Qué onda maje, todo bien"})


class PeticionLote(BaseModel):
    textos: list[str] = Field(..., min_length=1, max_length=LOTE_MAXIMO)


class Prediccion(BaseModel):
    texto_original: str
    texto_normalizado: str
    clase: str
    label: int
    confianza: float
    probabilidades: dict[str, float]
    nivel_de_riesgo: Literal["ninguno", "bajo", "alto", "crítico"]


RIESGO = {0: "ninguno", 1: "bajo", 2: "alto", 3: "crítico"}


def _predecir(textos: list[str]) -> list[Prediccion]:
    normalizados = [normalizar(t) for t in textos]
    enc = _estado["tok"](normalizados, return_tensors="pt", truncation=True,
                         max_length=MAX_LEN, padding=True).to(_estado["dev"])
    with torch.no_grad():
        logits = _estado["mod"](**enc).logits.float().cpu().numpy()
    probs = np.exp(logits - logits.max(-1, keepdims=True))
    probs /= probs.sum(-1, keepdims=True)

    salida = []
    for original, norm, p in zip(textos, normalizados, probs):
        i = int(p.argmax())
        salida.append(Prediccion(
            texto_original=original, texto_normalizado=norm,
            clase=CLASES[i], label=i, confianza=round(float(p[i]), 4),
            probabilidades={c: round(float(v), 4) for c, v in zip(CLASES, p)},
            nivel_de_riesgo=RIESGO[i]))
    return salida


@app.get("/salud")
def salud():
    return {"estado": "ok", "modelo": str(MODELO), "dispositivo": str(_estado.get("dev")),
            "clases": CLASES, "contrato": _estado.get("contrato", {})}


@app.post("/clasificar", response_model=Prediccion)
def clasificar(p: Peticion):
    if not p.texto.strip():
        raise HTTPException(400, "El texto está vacío.")
    return _predecir([p.texto])[0]


@app.post("/clasificar-lote", response_model=list[Prediccion])
def clasificar_lote(p: PeticionLote):
    vacios = [i for i, t in enumerate(p.textos) if not t.strip()]
    if vacios:
        raise HTTPException(400, f"Textos vacíos en las posiciones {vacios}.")
    t0 = time.perf_counter()
    r = _predecir(p.textos)
    app.extra = {"ms": round((time.perf_counter() - t0) * 1000, 1)}
    return r


@app.get("/")
def interfaz():
    ui = RAIZ / "app/ui/index.html"
    if not ui.exists():
        raise HTTPException(404, "Interfaz no encontrada.")
    return FileResponse(ui)
