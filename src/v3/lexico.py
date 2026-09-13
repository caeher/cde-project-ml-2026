# -*- coding: utf-8 -*-
"""
Acceso al léxico salvadoreño agrupado por familia canónica.

El CSV trae 2,035 filas que en realidad son ~114 palabras con sus variantes de
ofuscación. La nota del etiquetador dice de qué palabra es variante cada fila,
así que se puede reconstruir la familia. Trabajar por familia —y no por fila—
es lo que permite controlar la gramática: la concordancia depende de la palabra
canónica, no de cómo esté deformada.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
_PAT = re.compile(r"[Vv]ariante de ['\"]([^'\"]+)['\"]")


@dataclass
class Familia:
    canon: str
    clase: str
    subclase: str
    variantes: list[str] = field(default_factory=list)

    @property
    def label(self) -> int:
        return {"No Tóxico": 0, "Lenguaje Ofensivo": 1, "Discurso de Odio": 2,
                "Amenazas / Violencia Directa": 3, "Amenazas/Violencia": 3}[self.clase]


# Sustituciones habituales en la ofuscación salvadoreña, para validar que una
# variante de verdad pertenece a su familia y no es una fila corrupta del CSV.
_EQUIV = [set("ckqx"), set("bv"), set("szx"), set("ij1!"), set("ae4@"), set("o0"), set("gq")]


def _misma_inicial(a: str, b: str) -> bool:
    if a == b:
        return True
    return any(a in g and b in g for g in _EQUIV)


def _variante_plausible(v: str, canon: str) -> bool:
    """Descarta filas truncadas hasta el sinsentido ('07' como variante de 'cerote')."""
    v = v.strip()
    if len(v) < 3:
        return False
    letras = [c for c in v.lower() if c.isalnum()]
    if not letras:
        return False
    return _misma_inicial(letras[0], canon[0].lower())


def cargar() -> dict[str, Familia]:
    d = pd.read_csv(RAIZ / "data/raw/lexicon_salvadoreno.csv")
    d.columns = [c.lstrip("﻿") for c in d.columns]
    d = d[d["Texto_Original"].notna()].copy()
    canon = []
    for t, n in zip(d["Texto_Original"], d["Notas_Etiquetador"]):
        m = _PAT.search(str(n))
        canon.append(m.group(1).strip().lower() if m else str(t).strip().lower())
    d["canon"] = canon

    # Filas marcadas por el propio etiquetador como detección espuria
    d = d[~d["Notas_Etiquetador"].astype(str).str.contains("falso positivo", case=False)]

    fams: dict[str, Familia] = {}
    for c, sub in d.groupby("canon"):
        fila = sub.iloc[0]
        vs = sorted({str(x).strip() for x in sub["Texto_Original"]
                     if _variante_plausible(str(x).strip(), c)})
        if not vs:
            continue
        fams[c] = Familia(canon=c, clase=str(fila["Clase_Toxicidad"]),
                          subclase=str(fila["Subclase_Toxicidad"]), variantes=vs)
    return fams


if __name__ == "__main__":
    f = cargar()
    print(f"{len(f)} familias, {sum(len(x.variantes) for x in f.values())} variantes")
    for k in ["cerote", "puta", "matar", "inmigrante"]:
        if k in f:
            print(f"  {k:12s} [{f[k].subclase}] {f[k].variantes[:8]} ...")
