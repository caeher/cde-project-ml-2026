# -*- coding: utf-8 -*-
"""Métricas compartidas por todos los scripts de evaluación.

Antes vivían dentro de scripts con versión (comparar_v4.py y comparar_modelos.py); esos módulos las
siguen re-exportando, así que los imports viejos funcionan igual.
"""
import numpy as np
from scipy import stats
from sklearn.metrics import f1_score


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
