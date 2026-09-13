# -*- coding: utf-8 -*-
"""
Tokens de dominio para extender el vocabulario del modelo.

El análisis de tokenizadores mostró que ningún candidato cubre el dialecto:
el mejor reconoce el 5.6 % del léxico como token entero, y los placeholders de
emoji se parten en siete pedazos (`:pistola:` -> `▁:` `pis` `tola` `:`). Ese
troceado es la explicación más simple del 0/12 en emojis de amenaza: el modelo
nunca ve el emoji, ve fragmentos sin relación con él.

Añadir estas cadenas como tokens no entrena nada por sí solo — sus embeddings
nacen aleatorios — pero le da al modelo una unidad estable que aprender, en vez
de una secuencia distinta según el contexto.
"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar
from src.v3.lexico import cargar as cargar_lexico

PLACEHOLDERS = ["@usuario", "http://url", "correo@ejemplo.com", "0000-0000"]


def tokens_emoji() -> list[str]:
    """Los :nombre: que produce el normalizador para el catálogo del proyecto."""
    d = pd.read_csv(RAIZ / "data/dataset_b2/lexicon_emojis.csv")
    d.columns = [c.lstrip("﻿") for c in d.columns]
    out: set[str] = set()
    for e in d["emoji"]:
        for tk in normalizar(str(e)).split():
            if tk.startswith(":") and tk.endswith(":") and len(tk) > 2:
                out.add(tk)
    # los benignos que usa el generador, para que el par mínimo sea simétrico
    for e in ["❤️", "😂", "🎉", "🙏", "👏", "☕", "⚽", "🌮", "🥳", "😊", "🌻",
              "🎂", "🤝", "💪", "🌟", "🍀", "🖕", "💩", "🤡", "😡"]:
        for tk in normalizar(e).split():
            if tk.startswith(":") and tk.endswith(":") and len(tk) > 2:
                out.add(tk)
    return sorted(out)


def tokens_jerga(min_frecuencia: int = 3) -> list[str]:
    """
    Formas canónicas del léxico salvadoreño. Solo las canónicas: añadir las
    1,979 variantes ofuscadas sería contraproducente, porque la ofuscación debe
    quedar reconocible POR SUS PARTES —así generaliza a deformaciones nuevas—
    mientras que la palabra base sí merece ser una unidad.
    """
    fams = cargar_lexico()
    return sorted({f.canon for f in fams.values()
                   if " " not in f.canon and len(f.canon) >= 4})


def todos() -> list[str]:
    return PLACEHOLDERS + tokens_emoji() + tokens_jerga()


if __name__ == "__main__":
    e, j = tokens_emoji(), tokens_jerga()
    print(f"placeholders : {len(PLACEHOLDERS)}")
    print(f"emoji        : {len(e)}  -> {e[:10]}")
    print(f"jerga        : {len(j)}  -> {j[:14]}")
    print(f"TOTAL        : {len(todos())}")
    from transformers import AutoTokenizer
    for m in ["cardiffnlp/twitter-xlm-roberta-base", "pysentimiento/robertuito-base-cased"]:
        tok = AutoTokenizer.from_pretrained(m)
        antes = sum(len(tok.tokenize(t)) for t in todos())
        print(f"\n{m}")
        print(f"  subtokens que hoy consumen esas {len(todos())} cadenas: {antes}")
        print(f"  ejemplo ':pistola:' -> {tok.tokenize(':pistola:')}")
        print(f"  ejemplo 'cerote'    -> {tok.tokenize('cerote')}")
