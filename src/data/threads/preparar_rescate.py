# -*- coding: utf-8 -*-
"""Prepara los lotes que faltan para terminar la anotación de la ronda 3, a partir del estado de ronda3_consolidado.csv.

  --fase ab : lotes_R3A_NNN (textos sin etiqueta de A) y lote_R3B_NNN (textos sin etiqueta de B), de hasta --tam textos, mezclados con semilla fija
              (el anotador no ve el hilo ni el grupo). Un texto sin ninguna etiqueta va a un lote A y a uno B.
  --fase c  : lote_R3C_NNN con los textos en estado «desacuerdo_pendiente» (A ≠ B, sin desempate), de hasta --tam textos. Sin etiquetas de A ni B.
Antes de usarlo, ejecutar consolidar_ronda3.py para que el estado esté al día. Después de anotar, volver a ejecutar consolidar_ronda3.py.
Uso: python src/data/threads/preparar_rescate.py --fase ab
"""
import argparse, glob, os, sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402

B = P.THREADS / "blind" / "ronda3"


def escribe(df, prefijo, tam, semilla):
    df = df.sample(frac=1, random_state=semilla).reset_index(drop=True)
    nombres = []
    for k, i in enumerate(range(0, len(df), tam), 1):
        nombre = f"{prefijo}_{k:03d}"
        df.iloc[i:i + tam][["ID", "texto"]].to_csv(B / f"lote_{nombre}.csv", index=False, encoding="utf-8-sig")
        nombres.append((nombre, len(df.iloc[i:i + tam])))
    return nombres


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fase", choices=["ab", "c"], required=True); ap.add_argument("--tam", type=int, default=500)
    x = ap.parse_args()
    d = pd.read_csv(P.THREAD_LABELS / "ronda3_consolidado.csv", encoding="utf-8-sig", dtype={"ID": str})
    for f in glob.glob(str(B / f"lote_R3{'C' if x.fase == 'c' else '[AB]'}_*.csv")): os.remove(f)  # lotes de rescate anteriores: se regeneran desde el estado actual
    for f in glob.glob(str(B / ("salida_R3C_*" if x.fase == "c" else "salida_R3[AB]_*"))): os.remove(f)
    if x.fase == "ab":
        sin_a, sin_b = d[d.a.isna()], d[d.b.isna()]
        L = escribe(sin_a, "R3A", x.tam, 11) + escribe(sin_b, "R3B", x.tam, 12)
        print(f"sin etiqueta de A: {len(sin_a):,} · sin etiqueta de B: {len(sin_b):,}")
    else:
        pend = d[d.estado == "desacuerdo_pendiente"]
        L = escribe(pend, "R3C", x.tam, 13); print(f"desacuerdos pendientes: {len(pend):,}")
    print(f"{len(L)} lotes:", ", ".join(f"{n} ({m})" for n, m in L))


if __name__ == "__main__":
    main()
