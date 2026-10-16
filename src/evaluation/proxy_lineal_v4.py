# -*- coding: utf-8 -*-
"""
Proxy lineal (TF-IDF palabra 1-2 + LinearSVC balanceado, semilla 42), la configuración
del baseline clásico de notebooks/02. Mide la DIRECCIÓN del efecto de los datos de
octubre; no sustituye el reentrenamiento de RoBERTuito.

Uso: python src/evaluation/proxy_lineal_v4.py <dir_dataset> [--pesos]
  --pesos  aplica los pesos por muestra de la receta (real 1, sintético 0.75)
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.evaluation.comparar_modelos import mcnemar

D = Path(sys.argv[1]); PESOS = "--pesos" in sys.argv
tr, te = pd.read_csv(D / "train.csv"), pd.read_csv(D / "test.csv")
y = te.label.values
f1 = lambda a, b: f1_score(a, b, average="macro")

def ajustar(d):
    w = None
    if PESOS:
        o = d.origen.astype(str); w = np.where(o.str.startswith("real"), 1.0, 0.75)
    m = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    X = m.fit_transform(d.texto_modelo.astype(str))
    c = LinearSVC(class_weight="balanced", random_state=42).fit(X, d.label, sample_weight=w)
    return c.predict(m.transform(te.texto_modelo.astype(str)))

pb = ajustar(tr[tr.origen != "real_x_oct2026"]); pv = ajustar(tr)
r = {"dataset": str(D), "pesos": PESOS, "n_base": int((tr.origen != "real_x_oct2026").sum()), "n_v4": len(tr)}
print(f"{D}  pesos={PESOS}  train base {r['n_base']} · v4 {r['n_v4']}")
for nom, mk in [("total", np.ones(len(y), bool)), ("X", (te.Plataforma == "X").values), ("Facebook", (te.Plataforma == "Facebook").values)]:
    m = mcnemar(pb[mk] == y[mk], pv[mk] == y[mk])
    r[nom] = {"n": int(mk.sum()), "base": round(f1(y[mk], pb[mk]), 4), "v4": round(f1(y[mk], pv[mk]), 4),
              "b": m["b"], "c": m["c"], "p": round(float(m["p_exacta"]), 4)}
    print(f"  {nom:<9} n={mk.sum():<4} sin octubre {r[nom]['base']:.4f}  con octubre {r[nom]['v4']:.4f}  "
          f"Δ {r[nom]['v4'] - r[nom]['base']:+.4f}  b/c {m['b']}/{m['c']}  p={m['p_exacta']:.4f}")
print(json.dumps(r, ensure_ascii=False))
