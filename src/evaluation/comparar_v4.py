# -*- coding: utf-8 -*-
"""
Comparación pareada v4 (con datos de octubre) vs línea base (peso_nuevos 0).

Todo se recalcula desde las probabilidades y predicciones guardadas por
src/train/entrenar_v4.py; no se lee ninguna cifra de metricas.json.

Uso:
    python src/evaluation/comparar_v4.py --base runs/base --v4 runs/v4 \
        --test data/dataset_v4_e2/test.csv --adv data/dataset_v4_e2/test_adversarial.csv
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
META = 0.80


def f1m(y, p):
    return f1_score(y, p, average="macro", labels=[0, 1, 2, 3], zero_division=0)


def ic_f1(y, p, n=4000, seed=42):
    """Igual que src/v3/ensemble.py: 4000 remuestreos, semilla 42, percentiles 2.5/97.5."""
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        v.append(f1m(y[i], p[i]))
    return np.percentile(v, [2.5, 97.5])


def ic_delta(y, pa, pb, n=5000, seed=42):
    """Bootstrap pareado de Δ = F1(b) − F1(a), mismos índices para ambos."""
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 4:
            continue
        v.append(f1m(y[i], pb[i]) - f1m(y[i], pa[i]))
    v = np.array(v)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)), float((v <= 0).mean())


def cargar(run: Path, test, adv):
    semillas = sorted(p for p in run.glob("semilla_*") if (p / "probs_test.npy").exists())
    pt = [np.load(s / "probs_test.npy") for s in semillas]
    pa = [np.load(s / "probs_adv.npy") for s in semillas]
    pred = np.mean(pt, 0).argmax(1)
    # Control cruzado: lo recalculado debe coincidir con el CSV que escribió el entrenador
    csv = pd.read_csv(run / "preds_test.csv")
    assert (csv.ID.values == test.ID.values).all(), f"{run}: orden de ID distinto al test"
    assert (csv.y_pred.values == pred).all(), f"{run}: preds_test.csv no coincide con las probabilidades"
    return {"semillas": [s.name for s in semillas],
            "pred": pred, "pred_adv": np.mean(pa, 0).argmax(1),
            "f1_semillas": [f1m(test.label.values, p.argmax(1)) for p in pt]}


def fila(nombre, a, b, fmt="{:.4f}"):
    return f"  {nombre:<34}{fmt.format(a):>14}{fmt.format(b):>14}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--v4", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--adv", required=True)
    ap.add_argument("--salida", default=None, help="JSON con todas las cifras")
    a = ap.parse_args()

    te, adv = pd.read_csv(a.test), pd.read_csv(a.adv)
    y, ya = te.label.values, adv.label_esperado.values
    R = {"base": cargar(Path(a.base), te, adv), "v4": cargar(Path(a.v4), te, adv)}
    pa, pb = R["base"]["pred"], R["v4"]["pred"]
    out = {"n_test": len(y), "n_bateria": len(ya)}

    print("=" * 64)
    print(f"  LÍNEA BASE (sin octubre) vs V4 (con octubre) · test n = {len(y)}")
    print("=" * 64)
    print(f"  {'':<34}{'base':>14}{'v4':>14}")

    # 1. F1 global con IC
    print("\n[1] F1-macro del ensemble (IC 95 % bootstrap, 4000)")
    for k in ("base", "v4"):
        p = R[k]["pred"]; lo, hi = ic_f1(y, p)
        out[k] = {"f1": f1m(y, p), "ic95": [float(lo), float(hi)], "aciertos": int((p == y).sum()),
                  "f1_semillas": R[k]["f1_semillas"], "semillas": R[k]["semillas"]}
    for k_, lab in [("f1", "F1-macro"), ("aciertos", "aciertos / 460")]:
        print(fila(lab, out["base"][k_], out["v4"][k_], "{:.4f}" if k_ == "f1" else "{:d}"))
    print(f"  {'IC 95 %':<34}{'[%.4f, %.4f]' % tuple(out['base']['ic95']):>14}  "
          f"{'[%.4f, %.4f]' % tuple(out['v4']['ic95']):>14}")
    print(f"  {'extremo inferior ≥ 0.80':<34}{'sí' if out['base']['ic95'][0] >= META else 'NO':>14}"
          f"{'sí' if out['v4']['ic95'][0] >= META else 'NO':>14}")
    sb, sv = np.array(out["base"]["f1_semillas"]), np.array(out["v4"]["f1_semillas"])
    print(f"  {'semillas sueltas (media ± de)':<30}{'%.4f ± %.4f' % (sb.mean(), sb.std(ddof=1)):>18}"
          f"{'%.4f ± %.4f' % (sv.mean(), sv.std(ddof=1)):>18}")
    print(f"  {'semillas sueltas (cada una)':<30}{' '.join('%.4f' % x for x in sb):>24}   {' '.join('%.4f' % x for x in sv)}")

    # 2. Prueba pareada global
    m = mcnemar(pa == y, pb == y); lo, hi, p_le0 = ic_delta(y, pa, pb)
    out["pareada"] = {"delta_f1": f1m(y, pb) - f1m(y, pa), "ic95_delta": [lo, hi],
                      "mcnemar": {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in m.items()}}
    print("\n[2] Comparación pareada global")
    print(f"  Δ F1 (v4 − base) = {out['pareada']['delta_f1']:+.4f}   IC 95 % pareado [{lo:+.4f}, {hi:+.4f}]")
    print(f"  McNemar ({m['metodo']}): solo v4 acierta b = {m['b']} · solo base acierta c = {m['c']} · "
          f"p = {m['p_exacta']:.4f}")
    print(f"  -> {'diferencia significativa' if m['significativo'] else 'sin diferencia significativa'}; "
          f"el IC del Δ {'cruza' if lo <= 0 <= hi else 'NO cruza'} el cero")

    # 3. Por plataforma
    print("\n[3] Por plataforma (F1-macro, IC del Δ pareado, McNemar)")
    out["plataforma"] = {}
    for plat in sorted(te.Plataforma.dropna().unique()):
        mk = (te.Plataforma == plat).values
        fa, fb = f1m(y[mk], pa[mk]), f1m(y[mk], pb[mk])
        mm = mcnemar(pa[mk] == y[mk], pb[mk] == y[mk]); l2, h2, _ = ic_delta(y[mk], pa[mk], pb[mk])
        out["plataforma"][plat] = {"n": int(mk.sum()), "base": fa, "v4": fb, "delta": fb - fa,
                                   "ic95_delta": [l2, h2], "mcnemar_p": float(mm["p_exacta"]),
                                   "b": mm["b"], "c": mm["c"]}
        print(f"  {plat:<9} n={mk.sum():<4} base {fa:.4f}  v4 {fb:.4f}  Δ {fb - fa:+.4f} "
              f"[{l2:+.4f}, {h2:+.4f}]  b/c {mm['b']}/{mm['c']}  p={mm['p_exacta']:.4f}")

    # 4. Por clase
    print("\n[4] F1 por clase")
    out["clase"] = {}
    fa_c = f1_score(y, pa, average=None, labels=[0, 1, 2, 3], zero_division=0)
    fb_c = f1_score(y, pb, average=None, labels=[0, 1, 2, 3], zero_division=0)
    for i, c in enumerate(CLASES):
        out["clase"][c] = {"n": int((y == i).sum()), "base": float(fa_c[i]), "v4": float(fb_c[i])}
        print(f"  {c:<20} n={int((y == i).sum()):<4} base {fa_c[i]:.4f}  v4 {fb_c[i]:.4f}  Δ {fb_c[i] - fa_c[i]:+.4f}")

    # 5. FPR sobre No Tóxico, con y sin jerga
    print("\n[5] FPR sobre No Tóxico (No Tóxico predicho como tóxico)")
    out["fpr"] = {}
    nt = y == 0
    for nom, mk in [("con jerga", te.n_jerga.fillna(0).values > 0), ("sin jerga", te.n_jerga.fillna(0).values == 0)]:
        s = nt & mk; n = int(s.sum())
        ka, kb = int((pa[s] != 0).sum()), int((pb[s] != 0).sum())
        out["fpr"][nom] = {"n": n, "fp_base": ka, "fp_v4": kb,
                           "base": ka / n if n else None, "v4": kb / n if n else None}
        print(f"  {nom:<10} n={n:<4} base {ka}/{n} = {ka / n:.3f}   v4 {kb}/{n} = {kb / n:.3f}"
              + ("   (n < 30: sin potencia)" if n < 30 else ""))

    # 6. Sarcasmo e ironía (los puntos débiles de la Etapa II)
    print("\n[6] Cortes débiles de la Etapa II")
    out["cortes"] = {}
    for col in ["Presencia_Sarcasmo", "Presencia_Ironia"]:
        mk = te[col].astype(str).str.strip().str.upper().isin(["SI", "SÍ"]).values
        if mk.sum():
            fa, fb = f1m(y[mk], pa[mk]), f1m(y[mk], pb[mk]); ac_a, ac_b = (pa[mk] == y[mk]).sum(), (pb[mk] == y[mk]).sum()
            out["cortes"][col] = {"n": int(mk.sum()), "base": fa, "v4": fb, "aciertos_base": int(ac_a), "aciertos_v4": int(ac_b)}
            print(f"  {col:<20} n={mk.sum():<4} F1 base {fa:.4f}  v4 {fb:.4f}   aciertos {ac_a} → {ac_b}")

    # 7. Batería adversarial por grupo
    print("\n[7] Batería adversarial (144)")
    ba, bb = R["base"]["pred_adv"] == ya, R["v4"]["pred_adv"] == ya
    mb = mcnemar(ba, bb)
    out["bateria"] = {"base": int(ba.sum()), "v4": int(bb.sum()), "mcnemar_p": float(mb["p_exacta"]),
                      "b": mb["b"], "c": mb["c"], "grupos": {}}
    print(f"  total   base {ba.sum()}/{len(ya)}   v4 {bb.sum()}/{len(ya)}   b/c {mb['b']}/{mb['c']}  p={mb['p_exacta']:.4f}")
    for g, idx in adv.groupby("grupo_de_prueba").groups.items():
        idx = np.asarray(list(idx))
        out["bateria"]["grupos"][g] = {"n": len(idx), "base": int(ba[idx].sum()), "v4": int(bb[idx].sum())}
        print(f"  {g:<44} {ba[idx].sum():>3} → {bb[idx].sum():>3}  / {len(idx)}")

    if a.salida:
        Path(a.salida).write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))
        print(f"\nguardado: {a.salida}")


if __name__ == "__main__":
    main()
