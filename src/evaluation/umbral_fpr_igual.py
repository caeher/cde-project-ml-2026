# -*- coding: utf-8 -*-
"""Comparación a igual tasa de falsos positivos. A cada modelo se le suma un sesgo b al log-prob de No Tóxico,
elegido SOLO en val oficial para igualar el FPR de val de v3.4.0 (referencia). Luego una sola medición en el banco.
Salida: reports/final/umbral_fpr_igual.json"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import f1_score
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402
from src.evaluation.comparativa_final import M, probs, bk, va, te, yb, yv, yt  # noqa: E402
from src.evaluation.metrics import ic_delta  # noqa: E402

def pred(p, b): z = np.log(np.clip(p, 1e-12, 1)); z[:, 0] += b; return z.argmax(1)
fpr = lambda y, p: float((p[y == 0] != 0).mean())
ref = "v3.4.0 (API)"; obj = fpr(yv, probs(M[ref][0], "valF").argmax(1)); R = {"fpr_val_objetivo": obj}; Pb = {}
for n, (comp, *_ ) in M.items():
    pv, pb, pt = probs(comp, "valF"), probs(comp, "bancoF"), probs(comp, "testF")
    bs = np.linspace(-1, 4, 501); f = np.array([fpr(yv, pred(pv, b)) for b in bs])
    b = 0.0 if n == ref else float(bs[np.argmin(np.abs(f - obj) + 1e-6 * np.abs(bs))])
    p = pred(pb, b); Pb[n] = p
    R[n] = dict(sesgo=b, fpr_val=fpr(yv, pred(pv, b)), fpr_banco=fpr(yb, p), f1_banco=float(f1_score(yb, p, average="macro")),
                recall=[float((p[yb == c] == c).mean()) for c in range(4)], f1_val=float(f1_score(yv, pred(pv, b), average="macro")),
                f1_test=float(f1_score(yt, pred(pt, b), average="macro")))
for n in M:
    if n != ref: lo, hi, _ = ic_delta(yb, Pb[ref], Pb[n]); R[n]["ic_delta_vs_api"] = [lo, hi]
(RAIZ / "reports/final/umbral_fpr_igual.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
print("objetivo FPR val", round(obj, 3))
for n in M: r = R[n]; print(f"{n:14s} b={r['sesgo']:+.2f} FPRval {r['fpr_val']:.3f} FPRbanco {r['fpr_banco']:.3f} F1banco {r['f1_banco']:.3f} recOD {r['recall'][2]:.3f} recAM {r['recall'][3]:.3f} test {r['f1_test']:.3f} IC {np.round(r.get('ic_delta_vs_api',[]),3)}")
