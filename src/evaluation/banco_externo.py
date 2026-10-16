# -*- coding: utf-8 -*-
"""[Plan de mejora, fase 0] Banco externo REAL CONGELADO: único criterio principal de comparación entre versiones (sustituye a la batería de 144 como criterio de adopción).
Conjuntos con etiquetas de consenso de 3 anotadores y que NINGUNA versión ≥ v3.0.0 vio al entrenar:
  migrantes (307) · externo 2: fútbol, política, seguridad en El Salvador (650) · militares_pandilleros (203) · odio_lgbt_racismo_xeno (4 hilos, ~880).
Uso: python src/evaluation/banco_externo.py"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.combinar_modelos import probs_propio, cache  # noqa: E402
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_f1, ic_delta  # noqa: E402

BANCO = RAIZ / "data/evaluation/frozen_bank"
def cargar():
    """Banco CONGELADO (ver data/evaluation/frozen_bank/MANIFEST.json con los SHA-256). Nunca entra a entrenamiento ni a selección."""
    t = [pd.read_csv(BANCO / f"{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]]
    return pd.concat(t, ignore_index=True)[["banco", "texto_original", "label"]]
def main():
    b = cargar(); y = b.label.values; tx = b.texto_original.tolist(); n = len(b)
    print(f"Banco externo: n = {n} | clases NT/OF/OD/AM {np.bincount(y, minlength=4).tolist()} | por banco {b.banco.value_counts().to_dict()}")
    P = {v: cache(f"{v}__bancoF", lambda v=v: probs_propio(f"models/{v}", tx)) for v in ["v3.0.0", "v3.1.0", "v3.2.0-rc1", "v3.3.0-rc1"]}
    P["v3.2.0"] = (P["v3.1.0"] + P["v3.2.0-rc1"]) / 2; P["v3.3.0"] = (P["v3.2.0-rc1"] + P["v3.3.0-rc1"]) / 2
    pr = {k: v.argmax(1) for k, v in P.items()}; orden = ["v3.0.0", "v3.1.0", "v3.2.0", "v3.3.0"]
    print(f"\n{'versión':<9}{'acierto':>8}{'F1-macro [IC 95 %]':>26}   recall NT / OF / OD / AM   FPR(NT)")
    for k in orden:
        p = pr[k]; lo, hi = ic_f1(y, p)
        print(f"{k:<9}{(p == y).mean():>8.3f}{f1m(y, p):>12.4f} [{lo:.3f},{hi:.3f}]   " + " / ".join(f"{float((p[y == c] == c).mean()):.3f}" for c in range(4)) + f"   {float((p[y == 0] != 0).mean()):.3f}")
    print("\nPareado contra la versión anterior:")
    for a_, b_ in [("v3.0.0", "v3.1.0"), ("v3.1.0", "v3.2.0"), ("v3.2.0", "v3.3.0")]:
        m = mcnemar(pr[a_] == y, pr[b_] == y); lo, hi, _ = ic_delta(y, pr[a_], pr[b_])
        print(f"  {a_} → {b_}: ΔF1 {f1m(y, pr[b_]) - f1m(y, pr[a_]):+.4f} IC [{lo:+.3f},{hi:+.3f}] · McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.4f}")
    print("\nPor banco, F1-macro (solo informativo: clases raras en algunos):")
    for bk, g in b.groupby("banco"):
        i = g.index.values; print(f"  {bk:<10} n={len(i):<4} " + " | ".join(f"{k} {(pr[k][i] == y[i]).mean():.3f}" for k in orden))
if __name__ == "__main__":
    main()
