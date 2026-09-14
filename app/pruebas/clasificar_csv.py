# -*- coding: utf-8 -*-
"""
Clasifica un archivo completo y escribe los resultados.

    python3 app/pruebas/clasificar_csv.py entrada.csv salida.csv
    python3 app/pruebas/clasificar_csv.py entrada.csv salida.csv --columna texto
    python3 app/pruebas/clasificar_csv.py frases.txt salida.csv

Acepta CSV (usa la columna indicada, o la primera de texto que encuentre) y TXT
con una frase por línea. Si el archivo trae una columna `label` o `clase`,
además calcula el acierto, que es lo que convierte esto en una evaluación y no
solo en una clasificación.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

MODELO = RAIZ / "models/v3/final"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
CANDIDATAS = ["texto_modelo", "texto", "texto_original", "Texto_Original", "text"]


def cargar_entrada(ruta: Path, columna: str | None) -> pd.DataFrame:
    if ruta.suffix.lower() in (".txt", ".md"):
        lineas = [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
        return pd.DataFrame({"texto": lineas})
    d = pd.read_csv(ruta)
    d.columns = [c.lstrip("﻿") for c in d.columns]
    if columna:
        if columna not in d.columns:
            raise SystemExit(f"La columna '{columna}' no está. Hay: {list(d.columns)}")
        return d.rename(columns={columna: "texto"})
    for c in CANDIDATAS:
        if c in d.columns:
            return d.rename(columns={c: "texto"})
    obj = [c for c in d.columns if d[c].dtype == object]
    if not obj:
        raise SystemExit(f"No encontré columna de texto. Hay: {list(d.columns)}")
    return d.rename(columns={obj[0]: "texto"})


@torch.no_grad()
def clasificar(textos, bs=64):
    tok = AutoTokenizer.from_pretrained(str(MODELO))
    mod = AutoModelForSequenceClassification.from_pretrained(str(MODELO)).eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mod.to(dev)
    norm = [normalizar(str(t)) for t in textos]
    salida = []
    for i in range(0, len(norm), bs):
        enc = tok(norm[i:i + bs], return_tensors="pt", truncation=True,
                  max_length=128, padding=True).to(dev)
        salida.append(mod(**enc).logits.float().cpu().numpy())
        print(f"\r  {min(i + bs, len(norm))}/{len(norm)}", end="", file=sys.stderr)
    print(file=sys.stderr)
    log = np.concatenate(salida)
    p = np.exp(log - log.max(-1, keepdims=True))
    return norm, p / p.sum(-1, keepdims=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("salida")
    ap.add_argument("--columna", default=None)
    a = ap.parse_args()

    d = cargar_entrada(Path(a.entrada), a.columna)
    print(f"  {len(d)} textos desde {a.entrada}", file=sys.stderr)
    norm, probs = clasificar(d["texto"].tolist())

    d["texto_normalizado"] = norm
    d["label_predicho"] = probs.argmax(1)
    d["clase_predicha"] = [CLASES[i] for i in d["label_predicho"]]
    d["confianza"] = probs.max(1).round(4)
    for j, c in enumerate(CLASES):
        d[f"p_{c}"] = probs[:, j].round(4)
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(a.salida, index=False, encoding="utf-8-sig")

    print(f"\n  distribución de lo predicho:")
    for c, n in d["clase_predicha"].value_counts().items():
        print(f"    {c:20s} {n:5d}  ({n/len(d):5.1%})")

    # si el archivo trae la etiqueta verdadera, esto pasa a ser una evaluación
    col_y = next((c for c in ("label", "clase", "y", "label_esperado") if c in d.columns), None)
    if col_y is not None:
        y = d[col_y]
        if y.dtype == object:
            y = y.map({c: i for i, c in enumerate(CLASES)})
        ok = y.notna()
        if ok.any():
            from sklearn.metrics import classification_report, f1_score
            yv, pv = y[ok].astype(int), d["label_predicho"][ok]
            print(f"\n  F1-macro: {f1_score(yv, pv, average='macro', zero_division=0):.4f}"
                  f"   acierto: {(yv == pv).mean():.4f}  ({(yv == pv).sum()}/{ok.sum()})")
            print(classification_report(yv, pv, labels=range(4), target_names=CLASES,
                                        digits=4, zero_division=0))
    print(f"  -> {a.salida}")


if __name__ == "__main__":
    main()
