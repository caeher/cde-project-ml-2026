"""Carga compartida de XLM-R para la API y los scripts de Julio."""
from __future__ import annotations

import json
import os
from pathlib import Path

from src.paths import MODELS, ROOT

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
XLMR_HF_ID = "TheArbite/xlmr-large-hateval-hate-speech-sv"
XLMR_HF_REVISION = "9476aae3116cf3a2bde95b9a410284c5186a1f1f"
LOCAL_DIR = MODELS / "xlmr_hate_speech_sv"


def tiene_pesos(ruta: Path) -> bool:
    """La configuración y el tokenizador solos no son un modelo entrenado."""
    if not (ruta / "config.json").is_file():
        return False
    if any((ruta / n).is_file() for n in ("model.safetensors", "pytorch_model.bin")):
        return True
    for nombre in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        indice = ruta / nombre
        if indice.is_file():
            datos = json.loads(indice.read_text(encoding="utf-8"))
            shards = set(datos.get("weight_map", {}).values())
            if shards and all((ruta / shard).is_file() for shard in shards):
                return True
    return False


def resolver_local(ruta: str | Path | None = None) -> Path | None:
    seleccion = ruta if ruta is not None else os.environ.get("XLMR_MODEL_PATH")
    if seleccion is not None:
        destino = Path(seleccion).expanduser()
        if not destino.is_absolute():
            destino = ROOT / destino
        if not tiene_pesos(destino):
            raise FileNotFoundError(f"Modelo XLM-R incompleto en {destino}: faltan configuración o pesos.")
        return destino
    candidatos = (
        LOCAL_DIR,
        ROOT / "prototype" / "xlm_roberta_hate_speech_sv",
        ROOT / "prototype" / "mi_modelo_xlmr",
    )
    return next((p for p in candidatos if tiene_pesos(p)), None)


def cargar_xlmr(ruta: str | Path | None = None, *, solo_remoto: bool = False):
    """Devuelve tokenizador, modelo, dispositivo y procedencia de los pesos."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    local = None if solo_remoto else resolver_local(ruta)
    origen = str(local) if local is not None else XLMR_HF_ID
    opciones = {"local_files_only": True} if local is not None else {"revision": XLMR_HF_REVISION}
    tokenizer = AutoTokenizer.from_pretrained(origen, **opciones)
    model = AutoModelForSequenceClassification.from_pretrained(
        origen, low_cpu_mem_usage=True, **opciones
    )
    etiquetas = [model.config.id2label.get(i, model.config.id2label.get(str(i))) for i in range(4)]
    if model.config.num_labels != 4 or etiquetas not in (CLASES, [f"LABEL_{i}" for i in range(4)]):
        raise ValueError(f"Etiquetas incompatibles con el proyecto en {origen}: {etiquetas}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()
    return tokenizer, model, device, local
