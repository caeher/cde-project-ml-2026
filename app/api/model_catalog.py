"""Catálogo y descarga de los clasificadores publicados en Hugging Face.

Los pesos no forman parte del repositorio. ``snapshot_download`` los guarda en
la caché configurada y devuelve el snapshot local que luego consume
Transformers. Así el mismo código funciona en desarrollo, en Docker y en una
plataforma de deploy con almacenamiento persistente.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from huggingface_hub import snapshot_download


RAIZ = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "robertuito-v3-sv")
HF_CACHE_DIR = Path(
    os.getenv("HF_CACHE_DIR", str(RAIZ / "models" / ".hf-cache"))
)


@dataclass(frozen=True)
class ModelSpec:
    key: str
    repo_id: str
    nombre: str
    descripcion: str


MODEL_CATALOG: dict[str, ModelSpec] = {
    "mbert-sv": ModelSpec(
        key="mbert-sv",
        repo_id="caeher/mbert-sv",
        nombre="mBERT-SV",
        descripcion="BERT multilingüe ajustado al corpus salvadoreño",
    ),
    "robertuito-v3-sv": ModelSpec(
        key="robertuito-v3-sv",
        repo_id="caeher/robertuito-v3-sv",
        nombre="RoBERTuito V3-SV",
        descripcion="RoBERTuito ajustado a lenguaje de redes sociales",
    ),
    "twitter-xlm-roberta-v3-sv": ModelSpec(
        key="twitter-xlm-roberta-v3-sv",
        repo_id="caeher/twitter-xlm-roberta-v3-sv",
        nombre="Twitter-XLM-R V3-SV",
        descripcion="XLM-R preentrenado en publicaciones de Twitter",
    ),
    "xlm-roberta-base-b2-sv": ModelSpec(
        key="xlm-roberta-base-b2-sv",
        repo_id="caeher/xlm-roberta-base-b2-sv",
        nombre="XLM-R base B2-SV",
        descripcion="XLM-R base ajustado al corpus B2 salvadoreño",
    ),
}

# Solo se descargan los artefactos necesarios para inferencia. README, métricas
# y argumentos de entrenamiento no son necesarios para levantar la API.
MODEL_FILES = [
    "config.json",
    "inference_contract.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.json",
    "vocab.txt",
    "merges.txt",
    "sentencepiece.bpe.model",
]


def get_model_spec(model_key: str) -> ModelSpec:
    """Devuelve un modelo del catálogo o lanza un error claro."""
    try:
        return MODEL_CATALOG[model_key]
    except KeyError as exc:
        disponibles = ", ".join(MODEL_CATALOG)
        raise ValueError(
            f"Modelo desconocido: {model_key!r}. Disponibles: {disponibles}"
        ) from exc


def catalog_as_dicts(active_model: str | None = None) -> list[dict]:
    """Serializa el catálogo para el selector de la interfaz web."""
    return [
        {**asdict(spec), "activo": spec.key == active_model}
        for spec in MODEL_CATALOG.values()
    ]


def local_override() -> Path | None:
    """Ruta opcional para probar localmente sin volver a descargar pesos.

    Se activa con ``LOCAL_MODEL_PATH=models/v3/final``. En deploy no se usa
    porque la variable no se define y el origen siempre es Hugging Face.
    """
    raw = os.getenv("LOCAL_MODEL_PATH", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"LOCAL_MODEL_PATH no existe: {path}")
    return path


def download_model(model_key: str) -> Path:
    """Descarga o reutiliza desde caché el snapshot de un modelo."""
    spec = get_model_spec(model_key)
    override = local_override()
    if override is not None:
        return override

    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_download(
        repo_id=spec.repo_id,
        cache_dir=str(HF_CACHE_DIR),
        allow_patterns=MODEL_FILES,
    )
    return Path(snapshot)


def selected_model_keys(value: str | None = None) -> list[str]:
    """Interpreta ``PRELOAD_MODELS`` para el paso de build/deploy."""
    raw = (value if value is not None else os.getenv("PRELOAD_MODELS", "all")).strip()
    if not raw or raw.lower() in {"all", "*"}:
        return list(MODEL_CATALOG)
    if raw.lower() in {"none", "false", "0", "no"}:
        return []

    keys = [part.strip() for part in raw.split(",") if part.strip()]
    for key in keys:
        get_model_spec(key)
    return keys
