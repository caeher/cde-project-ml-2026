# -*- coding: utf-8 -*-
"""Temperature scaling del ensemble: T se ajusta SOLO en val; test se mide una vez.
Las probabilidades guardadas son el promedio de softmax; se calibra sobre log(p) (no cambia el argmax)."""
import sys, glob
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar

def ece(p, y, bins=10):
    conf, pred = p.max(1), p.argmax(1); e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.any(): e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return e

def escala(p, T):
    z = np.log(np.clip(p, 1e-12, 1)) / T; z -= z.max(1, keepdims=True)
    e = np.exp(z); return e / e.sum(1, keepdims=True)

def nll(p, y): return -np.log(p[np.arange(len(y)), y] + 1e-12).mean()

run, d = sys.argv[1], "data/history/v1.3.1"
yv, yt = pd.read_csv(f"{d}/val.csv").label.values, pd.read_csv(f"{d}/test.csv").label.values
L = lambda c: np.mean([np.load(f) for f in sorted(glob.glob(f"runs/{run}/semilla_*/probs_{c}.npy"))], 0)
pv, pt = L("val"), L("test")
T = minimize_scalar(lambda t: nll(escala(pv, t), yv), bounds=(0.3, 5), method="bounded").x
print(f"{run}: T = {T:.3f} (ajustada en val)")
for n, p, y in [("val", pv, yv), ("test", pt, yt)]:
    q = escala(p, T)
    print(f"  {n}: ECE {ece(p,y):.4f} -> {ece(q,y):.4f} | NLL {nll(p,y):.4f} -> {nll(q,y):.4f} | argmax igual: {(p.argmax(1)==q.argmax(1)).all()}")
