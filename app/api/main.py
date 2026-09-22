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
import gc
import os
import sys
import threading
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
from app.api.model_catalog import (  # noqa: E402
    DEFAULT_MODEL,
    catalog_as_dicts,
    download_model,
    get_model_spec,
)
from src.features.normalization import normalizar

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MAX_LEN = 128
LOTE_MAXIMO = 64

_estado: dict = {}
_modelo_lock = threading.RLock()


def _cargar_modelo(modelo: str, ruta: Path | None = None) -> dict:
    """Descarga, carga y valida un modelo del catálogo."""
    spec = get_model_spec(modelo)
    ruta = ruta or download_model(modelo)
    tok = AutoTokenizer.from_pretrained(str(ruta), local_files_only=True)
    mod = AutoModelForSequenceClassification.from_pretrained(
        str(ruta), local_files_only=True
    ).eval()
    etiquetas = [mod.config.id2label.get(i, "") for i in range(len(CLASES))]
    if etiquetas != CLASES:
        raise RuntimeError(
            f"El modelo {spec.repo_id} no cumple el contrato de etiquetas: {etiquetas}"
        )

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mod.to(dev)
    contrato_path = ruta / "inference_contract.json"
    contrato = json.loads(contrato_path.read_text(encoding="utf-8")) \
        if contrato_path.exists() else {}
    return {
        "key": modelo,
        "spec": spec,
        "path": ruta,
        "tok": tok,
        "mod": mod,
        "dev": dev,
        "contrato": contrato,
    }


def _activar_modelo(modelo: str) -> dict:
    """Deja un solo modelo activo para limitar el consumo de memoria."""
    with _modelo_lock:
        if _estado.get("key") == modelo:
            return _estado

        # La descarga ocurre antes de liberar el modelo actual: si falla la
        # red, la API conserva el modelo que ya estaba funcionando. Después
        # se liberan sus tensores para evitar que el cambio duplique el pico
        # de RAM en CPU.
        ruta = download_model(modelo)
        modelo_anterior = _estado.get("mod")
        tokenizer_anterior = _estado.get("tok")
        _estado.clear()
        del modelo_anterior, tokenizer_anterior
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        cargado = _cargar_modelo(modelo, ruta)
        _estado.update(cargado)
        return _estado


def _resumen_modelo() -> dict:
    actual = _estado.get("key")
    spec = _estado.get("spec")
    return {
        "id": actual,
        "nombre": spec.nombre if spec else None,
        "repo_id": spec.repo_id if spec else None,
        "dispositivo": str(_estado.get("dev")),
    }


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    precargar = os.getenv("PRELOAD_DEFAULT", "1").lower() not in {"0", "false", "no"}
    if precargar:
        _activar_modelo(DEFAULT_MODEL)
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
    modelo: str | None = Field(
        default=None,
        description="Clave del modelo. Si se omite se usa el modelo activo.",
    )


class PeticionLote(BaseModel):
    textos: list[str] = Field(..., min_length=1, max_length=LOTE_MAXIMO)
    modelo: str | None = Field(default=None)


class SeleccionModelo(BaseModel):
    modelo: str = Field(..., description="Clave del modelo publicado en Hugging Face")


class Prediccion(BaseModel):
    modelo: str
    texto_original: str
    texto_normalizado: str
    clase: str
    label: int
    confianza: float
    probabilidades: dict[str, float]
    nivel_de_riesgo: Literal["ninguno", "bajo", "alto", "crítico"]


RIESGO = {0: "ninguno", 1: "bajo", 2: "alto", 3: "crítico"}


def _predecir(textos: list[str], modelo: str | None = None) -> list[Prediccion]:
    with _modelo_lock:
        activo = modelo or _estado.get("key", DEFAULT_MODEL)
        estado = _activar_modelo(activo)
        normalizados = [normalizar(t) for t in textos]
        max_len = int(estado["contrato"].get("max_length", MAX_LEN))
        enc = estado["tok"](
            normalizados,
            return_tensors="pt",
            truncation=True,
            max_length=max_len,
            padding=True,
        ).to(estado["dev"])
        with torch.no_grad():
            logits = estado["mod"](**enc).logits.float().cpu().numpy()
        modelo_activo = estado["key"]
        probs = np.exp(logits - logits.max(-1, keepdims=True))
        probs /= probs.sum(-1, keepdims=True)

    salida = []
    for original, norm, p in zip(textos, normalizados, probs):
        i = int(p.argmax())
        salida.append(Prediccion(
            modelo=modelo_activo,
            texto_original=original, texto_normalizado=norm,
            clase=CLASES[i], label=i, confianza=round(float(p[i]), 4),
            probabilidades={c: round(float(v), 4) for c, v in zip(CLASES, p)},
            nivel_de_riesgo=RIESGO[i]))
    return salida


@app.get("/salud")
def salud():
    return {"estado": "ok", "modelo": _resumen_modelo(),
            "clases": CLASES, "contrato": _estado.get("contrato", {})}


@app.get("/modelos")
def modelos():
    """Lista los modelos disponibles para la interfaz."""
    return {"activo": _estado.get("key"), "modelos": catalog_as_dicts(_estado.get("key"))}


@app.post("/modelo")
def seleccionar_modelo(p: SeleccionModelo):
    """Descarga/carga y activa el modelo seleccionado."""
    try:
        estado = _activar_modelo(p.modelo)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"estado": "ok", "modelo": _resumen_modelo(),
            "modelos": catalog_as_dicts(estado["key"])}


@app.post("/clasificar", response_model=Prediccion)
def clasificar(p: Peticion):
    if not p.texto.strip():
        raise HTTPException(400, "El texto está vacío.")
    try:
        return _predecir([p.texto], p.modelo)[0]
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/clasificar-lote", response_model=list[Prediccion])
def clasificar_lote(p: PeticionLote):
    vacios = [i for i, t in enumerate(p.textos) if not t.strip()]
    if vacios:
        raise HTTPException(400, f"Textos vacíos en las posiciones {vacios}.")
    t0 = time.perf_counter()
    try:
        r = _predecir(p.textos, p.modelo)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    app.extra = {"ms": round((time.perf_counter() - t0) * 1000, 1)}
    return r


@app.get("/")
def interfaz():
    ui = RAIZ / "app/ui/index.html"
    if not ui.exists():
        raise HTTPException(404, "Interfaz no encontrada.")
    return FileResponse(ui)
