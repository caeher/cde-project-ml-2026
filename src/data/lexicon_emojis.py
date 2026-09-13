# -*- coding: utf-8 -*-
"""
Catálogo de emojis con uso discriminatorio — reconstruido.

PROBLEMA DE ORIGEN
------------------
`data/raw/lexicon_emojis.csv` se guardó desde Excel en codificación cp850 (DOS).
Las descripciones sobrevivieron con mojibake recuperable, pero **los glifos de los
emojis se convirtieron en literales `?`** y se perdieron de forma irreversible.

Este módulo restituye los glifos a partir de las descripciones textuales entre
paréntesis que sí sobrevivieron, y normaliza el esquema al de la taxonomía del
proyecto (4 clases canónicas), porque el archivo original usaba subclases como
clase igual que ocurría en el corpus.
"""
from __future__ import annotations

import pandas as pd

# Cada entrada: (emojis, descripción, clase canónica, subclase, grupos afectados)
CATALOGO = [
    (["🐒", "🐒🇲🇽", "🐒🇦🇷", "🐒🇪🇨", "🐒🇻🇪", "🐒🇭🇳", "🐒🇸🇻"],
     "Bestialización racial: comparar latinoamericanos con monos o simios",
     "Discurso de Odio", "Bestialización", "Latinoamericanos"),
    (["🧼🇮🇱", "🧼"],
     "Antisemitismo eliminacionista: alusión al Holocausto mediante el jabón",
     "Discurso de Odio", "Antisemitismo", "Judíos"),
    (["🧃"],
     "Juego de palabras 'jugo'/'judío' para evadir filtros de palabras",
     "Discurso de Odio", "Antisemitismo", "Judíos"),
    (["🍍"],
     "Cosificación sexual de menores encubierta",
     "Discurso de Odio", "Cosificación infantil", "Menores de edad"),
    (["🏳️‍🌈🤨", "🏳️‍🌈👀"],
     "Señalamiento burlesco de la orientación sexual o identidad de género",
     "Discurso de Odio", "Homofobia", "Personas LGBT"),
    (["🗣️👊🤤", "🤤"],
     "Insulto capacitista a la inteligencia",
     "Discurso de Odio", "Capacitismo", "Personas con discapacidad intelectual"),
    (["🤮🙈"],
     "Desprecio racial hacia personas de tez oscura",
     "Discurso de Odio", "Racismo", "Personas racializadas"),
    (["👴💀", "👴👻"],
     "Burla por edad avanzada",
     "Discurso de Odio", "Edadismo", "Adultos mayores"),
    (["🥷"],
     "Insulto racial hacia personas negras o morenas",
     "Discurso de Odio", "Racismo", "Afrodescendientes"),
    (["😈📕"],
     "Estigmatización de personas con baja escolaridad",
     "Discurso de Odio", "Clasismo", "Personas con baja educación"),
    (["🦶"],
     "Referencia despectiva a personas morenas",
     "Discurso de Odio", "Racismo", "Personas racializadas"),
    (["🙋‍♂️"],
     "Saludo nazi encubierto en discusiones sobre Israel",
     "Discurso de Odio", "Antisemitismo", "Judíos"),
    (["🐀", "🐁"],
     "Comparación con ratas: desprecio, suciedad, invasión",
     "Discurso de Odio", "Aporofobia", "Migrantes y personas empobrecidas"),
    (["🐷", "🐖"],
     "Comparación con cerdos: gordofobia o desprecio racial",
     "Discurso de Odio", "Gordofobia", "Personas con sobrepeso"),
    (["🐕", "🐶"],
     "Comparación con perros: sumisión o clase baja",
     "Discurso de Odio", "Aporofobia", "Personas en situación de pobreza"),
    (["🐍"],
     "Asociación con traición y maldad",
     "Lenguaje Ofensivo", "Tono Agresivo", "Individuo"),
    (["🧠❓", "🧠🚫"],
     "Burla sobre falta de inteligencia",
     "Discurso de Odio", "Capacitismo", "Personas con discapacidad intelectual"),
    (["💀"],
     "Deseo de muerte o burla por enfermedad grave",
     "Amenazas/Violencia", "Deseo de Daño", "Personas enfermas"),
    (["⚰️"],
     "Burla por muerte o enfermedad terminal",
     "Amenazas/Violencia", "Deseo de Daño", "Personas enfermas"),
    (["🧟"],
     "Deshumanización de seguidores políticos",
     "Lenguaje Ofensivo", "Descalificación Política", "Colectivo político"),
    (["🪳", "🪲"],
     "Comparación con cucarachas: desprecio extremo e invasión",
     "Discurso de Odio", "Aporofobia", "Migrantes y grupos étnicos"),
    (["🌑"],
     "Referencia despectiva encubierta a la tez oscura",
     "Discurso de Odio", "Racismo", "Personas racializadas"),
    (["🚽🧻", "🚽"],
     "Cosificación como desecho aplicada a personas",
     "Discurso de Odio", "Aporofobia", "Migrantes y personas empobrecidas"),
    (["👨‍🌾🐒"],
     "Burla racista hacia personas indígenas o campesinas",
     "Discurso de Odio", "Racismo", "Pueblos indígenas"),
    (["🇮🇱🤢"],
     "Rechazo antisemita disfrazado de crítica política",
     "Discurso de Odio", "Antisemitismo", "Judíos e israelíes"),
    (["🇺🇸🦅💩"],
     "Desprecio nacional hacia estadounidenses",
     "Lenguaje Ofensivo", "Crítica Institucional", "Estadounidenses"),
    (["🧹👷", "🧹"],
     "Eliminacionismo: 'barrer' o 'limpiar' a un grupo",
     "Amenazas/Violencia", "Incitación a la Violencia", "Migrantes y grupos étnicos"),
    (["🐋🚫", "🐋"],
     "Rechazo a personas con sobrepeso",
     "Discurso de Odio", "Gordofobia", "Personas con sobrepeso"),
    # --- Añadidos: emojis de amenaza ausentes del catálogo original ---
    (["🔫"], "Amenaza con arma de fuego", "Amenazas/Violencia", "Amenaza Directa", "Individuo"),
    (["🔪"], "Amenaza con arma blanca", "Amenazas/Violencia", "Amenaza Directa", "Individuo"),
    (["💣"], "Amenaza explosiva", "Amenazas/Violencia", "Amenaza Directa", "Colectivo"),
    (["🪦"], "Deseo de muerte", "Amenazas/Violencia", "Deseo de Daño", "Individuo"),
    (["⚱️"], "Deseo de muerte", "Amenazas/Violencia", "Deseo de Daño", "Individuo"),
]

# Emojis sin carga discriminatoria, necesarios como contraejemplo
EMOJIS_NEUTROS = [
    "❤️", "😊", "🙏", "👏", "🎉", "🥰", "😍", "💚", "🇸🇻", "⚽", "🎂", "🌻",
    "😂", "🤣", "👍", "🙌", "✨", "🥳", "☕", "🌮", "💪", "🫶", "😁", "🤗",
]

# Emojis de vulgaridad no dirigida a grupo protegido
EMOJIS_OFENSIVOS = ["🖕", "💩", "🤡", "😡", "🤬", "🙄", "🥱", "😒"]


def construir_catalogo() -> pd.DataFrame:
    """Devuelve el catálogo reconstruido como DataFrame plano."""
    filas = []
    for emojis, desc, clase, sub, grupos in CATALOGO:
        for e in emojis:
            filas.append({
                "emoji": e,
                "descripcion_uso": desc,
                "clase_asociada": clase,
                "subclase": sub,
                "grupos_afectados": grupos,
                "n_codepoints": len(e),
            })
    df = pd.DataFrame(filas).drop_duplicates(subset="emoji").reset_index(drop=True)
    df.insert(0, "ID", [f"EMO-{i+1:03d}" for i in range(len(df))])
    return df


def guardar(ruta="data/raw/lexicon_emojis_v2.csv"):
    df = construir_catalogo()
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    d = guardar()
    print(f"catálogo reconstruido: {len(d)} entradas")
    print(d.clase_asociada.value_counts().to_string())
