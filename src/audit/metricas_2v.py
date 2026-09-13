# -*- coding: utf-8 -*-
"""Métricas reproducidas a partir de los logits de reproducir_2v.py."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import (f1_score, accuracy_score, confusion_matrix,
                             precision_recall_fscore_support, log_loss)

RAIZ = Path("/home/willian/ues/esp/proyecto")
S = RAIZ / "reports/v2_auditoria"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MODS = ["mbert_v1", "mbert_b2", "xlmr_v1", "xlmr_mit"]


def leer(csv):
    df = pd.read_csv(RAIZ / csv)
    df.columns = [c.lstrip("﻿") for c in df.columns]
    return df


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


def ece(p, y, bins=10):
    conf, pred = p.max(1), p.argmax(1)
    acc = (pred == y).astype(float)
    e, n = 0.0, len(y)
    for lo in np.linspace(0, 1, bins + 1)[:-1]:
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.sum(): e += m.sum() / n * abs(acc[m].mean() - conf[m].mean())
    return e


def boot_f1(y, yp, n=2000, seed=42):
    r = np.random.default_rng(seed); idx = np.arange(len(y)); out = []
    for _ in range(n):
        s = r.choice(idx, len(idx), replace=True)
        if len(np.unique(y[s])) < 2: continue
        out.append(f1_score(y[s], yp[s], average="macro", zero_division=0))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), float(np.mean(out))


test = leer("data/dataset_b2/test.csv"); val = leer("data/dataset_b2/val.csv")
res = {}
print(f"{'modelo':10s} {'conj':5s} {'F1-macro':>9s} {'Acc':>7s} {'aciertos':>10s} {'ECE':>7s}")
for m in MODS:
    res[m] = {}
    for cj, df in (("test", test), ("val", val)):
        L = np.load(S / f"logits_{m}_{cj}.npy"); P = softmax(L)
        y = df["label"].values; yp = L.argmax(1)
        f1 = f1_score(y, yp, average="macro", zero_division=0); ac = accuracy_score(y, yp)
        res[m][cj] = dict(f1_macro=f1, accuracy=ac, aciertos=int((y == yp).sum()), n=len(y),
                          ece=ece(P, y), log_loss=float(log_loss(y, P, labels=[0,1,2,3])),
                          matriz=confusion_matrix(y, yp, labels=[0,1,2,3]).tolist())
        pr, rc, f1c, sp = precision_recall_fscore_support(y, yp, labels=[0,1,2,3], zero_division=0)
        res[m][cj]["por_clase"] = {CLASES[i]: dict(precision=pr[i], recall=rc[i], f1=f1c[i], soporte=int(sp[i])) for i in range(4)}
        if cj == "test":
            lo, hi, mu = boot_f1(y, yp); res[m][cj].update(boot_lo=lo, boot_hi=hi, boot_mean=mu)
        print(f"{m:10s} {cj:5s} {f1:9.4f} {ac:7.4f} {(y==yp).sum():5d}/{len(y):<4d} {res[m][cj]['ece']:7.4f}")

# cortes
print("\n--- por plataforma (test) ---")
for m in MODS:
    L = np.load(S / f"logits_{m}_test.npy"); yp = L.argmax(1); y = test["label"].values
    fila = []
    for pl in ["X", "Facebook"]:
        k = (test["Plataforma"] == pl).values
        f1 = f1_score(y[k], yp[k], average="macro", zero_division=0)
        fila.append(f"{pl} n={k.sum()} F1={f1:.4f}")
        res[m][f"plataforma_{pl}"] = dict(n=int(k.sum()), f1_macro=float(f1))
    print(f"{m:10s} " + " | ".join(fila))

print("\n--- FPR No Tóxico por jerga (test) ---")
for m in MODS:
    yp = np.load(S / f"logits_{m}_test.npy").argmax(1); y = test["label"].values
    for etiq, k in (("con jerga", (test["n_jerga"] > 0).values), ("sin jerga", (test["n_jerga"] == 0).values)):
        sel = k & (y == 0)
        fpr = float((yp[sel] != 0).mean())
        res[m][f"fpr_{etiq.replace(' ','_')}"] = dict(n=int(sel.sum()), fpr=fpr)
        print(f"{m:10s} {etiq:10s} n={sel.sum():3d} FPR={fpr:.4f}")

(S / "metricas_reproducidas.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

print("\n--- matrices de confusión (test, fila=real) ---")
for m in MODS:
    print(f"\n{m}")
    cm = np.array(res[m]["test"]["matriz"])
    print("            " + "".join(f"{c[:6]:>8s}" for c in CLASES))
    for i, c in enumerate(CLASES):
        print(f"{c[:11]:11s} " + "".join(f"{v:8d}" for v in cm[i]))

print("\n--- F1 por clase (test) ---")
print(f"{'clase':20s}" + "".join(f"{m:>12s}" for m in MODS))
for c in CLASES:
    print(f"{c:20s}" + "".join(f"{res[m]['test']['por_clase'][c]['f1']:12.4f}" for m in MODS))

print("\n--- IC bootstrap F1-macro (test) ---")
for m in MODS:
    r = res[m]["test"]; print(f"{m:10s} [{r['boot_lo']:.4f}, {r['boot_hi']:.4f}]  media {r['boot_mean']:.4f}")
