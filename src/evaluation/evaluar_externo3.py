# -*- coding: utf-8 -*-
"""Test externo 3 (590 textos de 3 hilos sobre pandilleros/CECOT; 173 de Amenazas). NINGÚN modelo entrenó con estos hilos.
Compara v3.0.0, v3.1.0, v3.2.0-rc1 y el ensamble v3.2.0 con IC y McNemar pareados."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.combinar_modelos import probs_propio, cache  # noqa: E402
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_delta, ic_f1  # noqa: E402
from sklearn.metrics import confusion_matrix

e = pd.read_csv(RAIZ / "data/hilos_reales/etiquetas/consenso_externo3.csv"); e = e[e.consenso >= 0].reset_index(drop=True)
y, tx = e.consenso.values, e.texto.tolist()
print("n =", len(y), "| clases", np.bincount(y, minlength=4).tolist())
P = {n: cache(f"{n}__ext3", lambda r=r: probs_propio(r, tx)) for n, r in [("v3.0.0", "models/v3.0.0"), ("v3.1.0", "models/v3.1.0"), ("v3.2.0-rc1", "models/v3.2.0-rc1")]}
P["v3.2.0 (ensamble)"] = (P["v3.1.0"] + P["v3.2.0-rc1"]) / 2
pr = {n: p.argmax(1) for n, p in P.items()}
for n, p in pr.items():
    lo, hi = ic_f1(y, p)
    print(f"{n:<20} acierto {(p == y).mean():.3f}  F1-macro {f1m(y, p):.4f} [{lo:.3f},{hi:.3f}] | recall NT/OF/OD/AM", [round(float((p[y == k] == k).mean()), 3) for k in range(4)],
          "| FPR sobre No Tóxico %.3f" % float((p[y == 0] != 0).mean()))
ref = pr["v3.1.0"]
for n in ["v3.0.0", "v3.2.0-rc1", "v3.2.0 (ensamble)"]:
    m = mcnemar(ref == y, pr[n] == y); lo, hi, _ = ic_delta(y, ref, pr[n])
    print(f"  {n:<20} vs v3.1.0: ΔF1 {f1m(y, pr[n]) - f1m(y, ref):+.4f} IC [{lo:+.3f},{hi:+.3f}] McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.4f}")
print("\nMatriz de confusión del ensamble v3.2.0:"); print(pd.DataFrame(confusion_matrix(y, pr["v3.2.0 (ensamble)"], labels=[0, 1, 2, 3]), index=["esp0", "esp1", "esp2", "esp3"], columns=["p0", "p1", "p2", "p3"]))
e["v3.1.0"], e["v3.2.0"] = pr["v3.1.0"], pr["v3.2.0 (ensamble)"]
e.to_csv(RAIZ / "data/hilos_reales/predicciones/eval_externo3.csv", index=False, encoding="utf-8-sig")
