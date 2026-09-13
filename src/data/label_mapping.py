"""
Consolidación de etiquetas al esquema canónico de 4 clases.

CONTEXTO DEL PROBLEMA
---------------------
`data/raw/corpus_salvadoreno.csv` contiene 16 valores distintos en
`Clase_Toxicidad` donde la taxonomía del proyecto define 4. El EDA revela que
NO se trata de ruido aleatorio: 348 de las 360 filas anómalas provienen de un
solo anotador (Julio), que aplicó el nivel de SUBCLASE en la columna de CLASE
(anotó "racismo", "xenofobia", "clasismo" en lugar de "Discurso de Odio").

Es una divergencia de protocolo entre anotadores, no un error de tipeo. La
consecuencia es que hay que documentar el remapeo de forma explícita y auditable
en lugar de resolverlo con un `.str.title()`.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Taxonomía canónica del proyecto
# --------------------------------------------------------------------------
CLASES_CANONICAS = [
    "No Tóxico",
    "Lenguaje Ofensivo",
    "Discurso de Odio",
    "Amenazas/Violencia",
]

ID2LABEL = dict(enumerate(CLASES_CANONICAS))
LABEL2ID = {v: k for k, v in ID2LABEL.items()}


# --------------------------------------------------------------------------
# Mapeo. La clave es la etiqueta cruda tal como aparece en el CSV.
# --------------------------------------------------------------------------
MAPEO_CLASES: dict[str, str] = {
    # --- Formas ya canónicas (incluye colisión de mayúsculas) ---
    "No Tóxico": "No Tóxico",
    "Lenguaje Ofensivo": "Lenguaje Ofensivo",
    "Discurso de odio": "Discurso de Odio",
    "Discurso de Odio": "Discurso de Odio",
    "Amenazas/Violencia": "Amenazas/Violencia",
    # --- Subclase usada como clase: ataques a grupo protegido -> Discurso de Odio ---
    # Criterio: la clase se define por el ATAQUE A UN GRUPO, no por el eje de
    # discriminación. El eje (racismo, xenofobia, ...) pertenece a `Subclase`.
    "racismo": "Discurso de Odio",
    "xenofobia": "Discurso de Odio",
    "clasismo": "Discurso de Odio",
    "religiofobia": "Discurso de Odio",
    "antisemitismo": "Discurso de Odio",
    # 'discriminacion' agrupa gordofobia, homofobia, capacitismo, misoginia,
    # serofobia, edadismo, transfobia: todos grupos protegidos.
    "discriminacion": "Discurso de Odio",
    # --- Insulto sin grupo protegido -> Lenguaje Ofensivo ---
    # Subclases observadas: "Descalificacion Politica", "Insulto directo",
    # "Descalificación deportiva". Ataque a individuo o entidad, no a grupo.
    "Insulto": "Lenguaje Ofensivo",
}

# --------------------------------------------------------------------------
# Casos que NO se resuelven automáticamente.
# Se marcan con `revisar_manual = True` en lugar de asignarles una clase por
# defecto. Son 7 filas: el coste de revisarlas a mano es trivial y el coste de
# equivocarse en una clase minoritaria no lo es.
# --------------------------------------------------------------------------
REQUIERE_REVISION: dict[str, str] = {
    "discriminacion_politica": (
        "La afiliación política no es categoría protegida en la mayoría de "
        "taxonomías de hate speech (Waseem & Hovy 2016; HatEval). Podría ser "
        "'Lenguaje Ofensivo'. Decidir y documentar en la guía de anotación."
    ),
    "incitacion_odio": (
        "Frontera entre 'Discurso de Odio' y 'Amenazas/Violencia'. Depende de si "
        "hay llamado explícito a la acción."
    ),
    "violencia_genero": (
        "Subclase 'misoginia'. Si es ataque a las mujeres como grupo -> Discurso "
        "de Odio; si es amenaza a una persona concreta -> Amenazas/Violencia."
    ),
    "violencia_psicologica": (
        "Subclase 'Estigmatización moral'. Probablemente 'Lenguaje Ofensivo', "
        "pero el término no existe en la taxonomía del proyecto."
    ),
}


# --------------------------------------------------------------------------
# Subclases: correcciones ortográficas y de codificación observadas.
# --------------------------------------------------------------------------
MAPEO_SUBCLASES: dict[str, str] = {
    "Estigmatizaciøn nacional": "Estigmatización nacional",
    "Estigmatizaciøn cultural": "Estigmatización cultural",
    "Discrimincacion etnica": "Discriminación étnica",
    "Discriminacion nacional/origen": "Discriminación por nacionalidad",
    "Discriminación por nacionalidad": "Discriminación por nacionalidad",
    "Discriminacion por discapacidad": "Capacitismo",
    "capacitismo": "Capacitismo",
    "Insulto directo": "Insulto Directo",
    "Insultos": "Insulto Directo",
    "Descalificacion directa": "Insulto Directo",
    "Descalificacion Politica": "Descalificación Política",
    "homofobia": "Homofobia",
    "misoginia": "Misoginia",
    "xenofobia": "Xenofobia",
    "aporofobia": "Aporofobia",
    "edadismo": "Edadismo",
    "gordofobia": "Gordofobia",
    "serofobia": "Serofobia",
    "bestialización": "Bestialización",
    "cosificacion": "Cosificación",
    "Eliminacionismo": "Eliminacionismo",
}


def mapear_clase(valor: str) -> tuple[str | None, bool]:
    """
    Devuelve (clase_canonica, requiere_revision).

    Si la etiqueta es ambigua devuelve (None, True): la fila se aparta para
    revisión humana en lugar de asignarle una clase arbitraria.
    """
    if not isinstance(valor, str):
        return None, True
    v = valor.strip()
    if v in MAPEO_CLASES:
        return MAPEO_CLASES[v], False
    if v in REQUIERE_REVISION:
        return None, True
    return None, True


def mapear_subclase(valor: str) -> str:
    """Canoniza la subclase; devuelve el valor original si no hay corrección."""
    if not isinstance(valor, str):
        return "N/A"
    v = valor.strip()
    return MAPEO_SUBCLASES.get(v, v)
