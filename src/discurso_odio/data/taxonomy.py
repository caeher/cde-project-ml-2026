"""Taxonomía de clases de toxicidad para el contexto salvadoreño."""

from __future__ import annotations

CANONICAL_LABELS: tuple[str, ...] = (
    "no_toxico",
    "ofensivo",
    "odio",
    "amenazas",
)

LABEL_TO_ID: dict[str, int] = {label: idx for idx, label in enumerate(CANONICAL_LABELS)}
ID_TO_LABEL: dict[int, str] = {idx: label for label, idx in LABEL_TO_ID.items()}

# Mapeo de etiquetas crudas del dataset → clases canónicas del perfil de proyecto.
RAW_LABEL_MAP: dict[str, str] = {
    "no toxico": "no_toxico",
    "no tóxico": "no_toxico",
    "no toxico ": "no_toxico",
    "no tóxico ": "no_toxico",
    "lenguaje ofensivo": "ofensivo",
    "insulto": "ofensivo",
    "discurso de odio": "odio",
    "discurso de odio ": "odio",
    "acoso": "odio",
    "amenazas/violencia": "amenazas",
    "amenazas / violencia": "amenazas",
    "otro": "ofensivo",
}


def normalize_label(raw_label: str | float | None) -> str:
    """Normaliza una etiqueta cruda a una de las 4 clases canónicas."""
    if raw_label is None or (isinstance(raw_label, float) and str(raw_label) == "nan"):
        return "no_toxico"
    key = str(raw_label).strip().lower()
    key = key.replace("ó", "o").replace("í", "i").replace("á", "a").replace("é", "e").replace("ú", "u")
    # Re-aplicar variantes con acentos ya normalizados
    key = key.replace("toxico", "toxico")
    mapped = RAW_LABEL_MAP.get(key)
    if mapped:
        return mapped
    # Fallback por palabras clave
    if "amenaza" in key or "violencia" in key:
        return "amenazas"
    if "odio" in key or "acoso" in key:
        return "odio"
    if "ofensivo" in key or "insulto" in key:
        return "ofensivo"
    if "no" in key and "toxic" in key:
        return "no_toxico"
    return "ofensivo"
