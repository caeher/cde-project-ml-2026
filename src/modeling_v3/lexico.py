# -*- coding: utf-8 -*-
"""Léxico salvadoreño agrupado por familia canónica (para augmentación futura)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from modeling_v3.paths import lexicon_salvadoreno_path

_PAT = re.compile(r"[Vv]ariante de ['\"]([^'\"]+)['\"]")


@dataclass
class Familia:
    canon: str
    clase: str
    subclase: str
    variantes: list[str] = field(default_factory=list)

    @property
    def label(self) -> int:
        return {
            "No Tóxico": 0,
            "Lenguaje Ofensivo": 1,
            "Discurso de Odio": 2,
            "Amenazas / Violencia Directa": 3,
            "Amenazas/Violencia": 3,
        }[self.clase]


_EQUIV = [set("ckqx"), set("bv"), set("szx"), set("ij1!"), set("ae4@"), set("o0"), set("gq")]


def _misma_inicial(a: str, b: str) -> bool:
    if a == b:
        return True
    return any(a in g and b in g for g in _EQUIV)


def _variante_plausible(v: str, canon: str) -> bool:
    v = v.strip()
    if len(v) < 3:
        return False
    letras = [c for c in v.lower() if c.isalnum()]
    if not letras:
        return False
    return _misma_inicial(letras[0], canon[0].lower())


def cargar(ruta: Path | None = None) -> dict[str, Familia]:
    p = ruta if ruta is not None else lexicon_salvadoreno_path()
    if not p.is_file():
        raise FileNotFoundError(
            f"No existe el léxico salvadoreño en {p}. "
            "Versione el archivo o use los splits congelados en data/processed/v3/."
        )
    d = pd.read_csv(p)
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    d = d[d["Texto_Original"].notna()].copy()
    canon = []
    for t, n in zip(d["Texto_Original"], d["Notas_Etiquetador"]):
        m = _PAT.search(str(n))
        canon.append(m.group(1).strip().lower() if m else str(t).strip().lower())
    d["canon"] = canon
    d = d[~d["Notas_Etiquetador"].astype(str).str.contains("falso positivo", case=False)]

    fams: dict[str, Familia] = {}
    for c, sub in d.groupby("canon"):
        fila = sub.iloc[0]
        vs = sorted(
            {
                str(x).strip()
                for x in sub["Texto_Original"]
                if _variante_plausible(str(x).strip(), c)
            }
        )
        if not vs:
            continue
        fams[c] = Familia(
            canon=c,
            clase=str(fila["Clase_Toxicidad"]),
            subclase=str(fila["Subclase_Toxicidad"]),
            variantes=vs,
        )
    return fams
