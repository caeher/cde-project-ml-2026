# -*- coding: utf-8 -*-
"""
Comparativa estadística entre dos modelos sobre el mismo conjunto de prueba.

Ejecuta la prueba de McNemar pareada, que es la correcta cuando ambos modelos se
evalúan sobre las MISMAS instancias. Comparar dos F1-macro sin prueba pareada no
permite concluir nada: la varianza del muestreo domina diferencias pequeñas.

USO
---
1) Cada responsable exporta un CSV con dos columnas: ID y y_pred

       import pandas as pd
       test = pd.read_csv("data/processed/test.csv")
       test["y_pred"] = mis_predicciones          # enteros 0..3, mismo orden
       test[["ID", "y_pred"]].to_csv("reports/preds_mbert.csv", index=False)

2) Se ejecuta la comparación

       python src/evaluation/comparar_modelos.py \
              reports/preds_mbert.csv reports/preds_xlmr.csv \
              --nombres mBERT XLM-R

REQUISITO
---------
Los dos archivos deben cubrir exactamente los mismos ID. El script aborta si no
es así, porque una prueba pareada sobre conjuntos distintos no es válida.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import classification_report, f1_score

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def mcnemar(correcto_a: np.ndarray, correcto_b: np.ndarray) -> dict:
    """
    McNemar pareada.

    b = casos que solo B acierta · c = casos que solo A acierta.
    Con discordancia baja (< 25) la binomial exacta es preferible a la
    aproximación chi-cuadrado, que se vuelve poco fiable.
    """
    b = int((correcto_b & ~correcto_a).sum())
    c = int((correcto_a & ~correcto_b).sum())
    n_disc = b + c
    if n_disc == 0:
        return {"b": 0, "c": 0, "discordantes": 0, "p_exacta": 1.0,
                "p_chi2": 1.0, "significativo": False, "metodo": "sin discordancia"}
    p_exacta = stats.binomtest(b, n_disc, 0.5).pvalue
    chi2 = (abs(b - c) - 1) ** 2 / n_disc
    p_chi2 = stats.chi2.sf(chi2, 1)
    return {
        "b": b, "c": c, "discordantes": n_disc,
        "p_exacta": p_exacta, "p_chi2": p_chi2,
        "significativo": bool(p_exacta < 0.05),
        "metodo": "binomial exacta" if n_disc < 25 else "chi-cuadrado con corrección",
    }


def bootstrap_diferencia(y, pa, pb, n=5000, semilla=42) -> dict:
    """IC bootstrap de la diferencia de F1-macro, remuestreando en pares."""
    rng = np.random.default_rng(semilla)
    difs = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < len(CLASES):
            continue
        difs.append(f1_score(y[i], pb[i], average="macro")
                    - f1_score(y[i], pa[i], average="macro"))
    difs = np.array(difs)
    lo, hi = np.percentile(difs, [2.5, 97.5])
    return {"dif_media": float(difs.mean()), "ic95": [float(lo), float(hi)],
            "cruza_cero": bool(lo <= 0 <= hi)}


def comparar(ruta_a, ruta_b, nombres, ruta_test, salida=None):
    test = pd.read_csv(ruta_test)
    A = pd.read_csv(ruta_a)[["ID", "y_pred"]].rename(columns={"y_pred": "pa"})
    B = pd.read_csv(ruta_b)[["ID", "y_pred"]].rename(columns={"y_pred": "pb"})

    d = test[["ID", "label", "Plataforma"]].merge(A, on="ID").merge(B, on="ID")
    if len(d) != len(test):
        raise SystemExit(
            f"ERROR: solo coinciden {len(d)} de {len(test)} ID. "
            "La prueba pareada exige exactamente las mismas instancias."
        )

    y, pa, pb = d.label.values, d.pa.values, d.pb.values
    na, nb = nombres
    f1a, f1b = f1_score(y, pa, average="macro"), f1_score(y, pb, average="macro")

    print("=" * 74)
    print(f"COMPARATIVA PAREADA: {na} vs {nb}   (n = {len(d)})")
    print("=" * 74)
    print(f"\n  F1-macro   {na}: {f1a:.4f}    {nb}: {f1b:.4f}    Δ = {f1b-f1a:+.4f}")
    print(f"  Accuracy   {na}: {(pa==y).mean():.4f}    {nb}: {(pb==y).mean():.4f}")
    print(f"  Aciertos   {na}: {(pa==y).sum()}       {nb}: {(pb==y).sum()}")

    m = mcnemar(pa == y, pb == y)
    print(f"\n--- McNemar ({m['metodo']}) ---")
    print(f"  b = {m['b']}  (solo {nb} acierta)")
    print(f"  c = {m['c']}  (solo {na} acierta)")
    print(f"  discordantes = {m['discordantes']} de {len(d)} ({m['discordantes']/len(d)*100:.1f}%)")
    print(f"  p exacta = {m['p_exacta']:.6f}   p chi2 = {m['p_chi2']:.6f}")
    print(f"  -> {'DIFERENCIA SIGNIFICATIVA' if m['significativo'] else 'SIN diferencia significativa (p >= 0.05)'}")

    bt = bootstrap_diferencia(y, pa, pb)
    print(f"\n--- Bootstrap pareado de la diferencia de F1-macro ---")
    print(f"  Δ medio = {bt['dif_media']:+.4f}   IC 95% = [{bt['ic95'][0]:+.4f}, {bt['ic95'][1]:+.4f}]")
    print(f"  -> el intervalo {'CRUZA el cero: sin evidencia de diferencia' if bt['cruza_cero'] else 'NO cruza el cero: diferencia consistente'}")

    print(f"\n--- Por plataforma ---")
    for plat in sorted(d.Plataforma.dropna().unique()):
        s = d[d.Plataforma == plat]
        ma = mcnemar((s.pa == s.label).values, (s.pb == s.label).values)
        print(f"  {plat:<10} n={len(s):<4} "
              f"{na}={f1_score(s.label,s.pa,average='macro'):.4f}  "
              f"{nb}={f1_score(s.label,s.pb,average='macro'):.4f}  "
              f"p={ma['p_exacta']:.4f}")

    print(f"\n--- Por clase (F1) ---")
    ra = classification_report(y, pa, output_dict=True, zero_division=0)
    rb = classification_report(y, pb, output_dict=True, zero_division=0)
    print(f"  {'clase':<20}{na:>10}{nb:>10}{'Δ':>9}")
    for i, c in enumerate(CLASES):
        fa, fb = ra[str(i)]["f1-score"], rb[str(i)]["f1-score"]
        print(f"  {c:<20}{fa:>10.4f}{fb:>10.4f}{fb-fa:>+9.4f}")

    if salida:
        pd.DataFrame([{
            "modelo_a": na, "modelo_b": nb, "n": len(d),
            "f1_a": round(f1a, 4), "f1_b": round(f1b, 4), "delta": round(f1b - f1a, 4),
            **{k: v for k, v in m.items()},
            "bootstrap_ic_lo": round(bt["ic95"][0], 4),
            "bootstrap_ic_hi": round(bt["ic95"][1], 4),
        }]).to_csv(salida, index=False, encoding="utf-8-sig")
        print(f"\nguardado: {salida}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="McNemar pareada entre dos modelos")
    ap.add_argument("preds_a")
    ap.add_argument("preds_b")
    ap.add_argument("--nombres", nargs=2, default=["modelo_A", "modelo_B"])
    ap.add_argument("--test", default="data/processed/test.csv")
    ap.add_argument("--salida", default="reports/comparativa_pareada.csv")
    a = ap.parse_args()
    comparar(a.preds_a, a.preds_b, a.nombres, a.test, a.salida)
