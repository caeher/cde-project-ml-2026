# -*- coding: utf-8 -*-
"""Compara un modelo candidato contra el modelo de referencia con 4 criterios FIJADOS ANTES de ver resultados.

  (a) test oficial: sin regresión significativa (McNemar pareado p >= 0.05 si el candidato baja)
  (b) batería de 144: no pierde más de 2 aciertos
  (c) hilo externo (nunca entrenado): mejora de F1-macro con IC 95 % pareado que NO cruza el cero
  (d) vulgaridad afectiva salvadoreña: afectivas → No Tóxico >= 17/20 e insultos detectados >= 16/18

Uso: python src/evaluation/comparar_candidato.py --cand models/v3.2.0 --ref models/v3.1.0 --externo data/history/v1.5.0/externo_migrantes.csv --nombre_extra migrantes
Necesita que ambos modelos tengan probs_test.npy y probs_adv.npy y que el candidato tenga probs_extra_<nombre>.npy.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_delta  # noqa: E402


def mp(run, nombre):
    return np.mean([np.load(f) for f in sorted(Path(run).glob(f"semilla_*/{nombre}.npy"))], 0)


def predecir_dir(ruta, textos):
    import app.api.main as M
    M._modelos.clear(); M.MODELOS = Path(ruta)
    return np.array([M.predecir(t)["label"] for t in textos])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True); ap.add_argument("--ref", required=True)
    ap.add_argument("--externo", required=True); ap.add_argument("--nombre_extra", default="migrantes")
    ap.add_argument("--dataset", default="data/history/v1.5.0")
    a = ap.parse_args(); D = RAIZ / a.dataset; R = {}
    te, adv = pd.read_csv(D / "test.csv"), pd.read_csv(D / "test_adversarial.csv"); y = te.label.values
    pr, pc = mp(a.ref, "probs_test").argmax(1), mp(a.cand, "probs_test").argmax(1)
    m = mcnemar(pr == y, pc == y); lo, hi, _ = ic_delta(y, pr, pc)
    R["a"] = dict(ref=f1m(y, pr), cand=f1m(y, pc), delta=f1m(y, pc) - f1m(y, pr), ic=[lo, hi], p=float(m["p_exacta"]), b=m["b"], c=m["c"])
    print(f"[a] test oficial  ref {R['a']['ref']:.4f}  cand {R['a']['cand']:.4f}  Δ {R['a']['delta']:+.4f}  IC [{lo:+.4f},{hi:+.4f}]  McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.3f}")
    ya = adv.label_esperado.values
    br, bc = int((mp(a.ref, "probs_adv").argmax(1) == ya).sum()), int((mp(a.cand, "probs_adv").argmax(1) == ya).sum())
    R["b"] = dict(ref=br, cand=bc); print(f"[b] batería 144   ref {br}  cand {bc}")
    ext = pd.read_csv(a.externo); ye = ext.label.values
    er = predecir_dir(a.ref, ext.texto_original); ec = mp(a.cand, f"probs_extra_{a.nombre_extra}").argmax(1)
    m2 = mcnemar(er == ye, ec == ye); lo2, hi2, _ = ic_delta(ye, er, ec)
    R["c"] = dict(ref=f1m(ye, er), cand=f1m(ye, ec), delta=f1m(ye, ec) - f1m(ye, er), ic=[lo2, hi2], p=float(m2["p_exacta"]))
    print(f"[c] hilo externo n={len(ye)}  ref F1 {R['c']['ref']:.4f} acierto {(er==ye).mean():.3f} | cand F1 {R['c']['cand']:.4f} acierto {(ec==ye).mean():.3f} | Δ {R['c']['delta']:+.4f} IC [{lo2:+.4f},{hi2:+.4f}] p={m2['p_exacta']:.4f}")
    print("    recall por clase  ref", [round(float((er[ye == k] == k).mean()), 3) for k in range(4)], " cand", [round(float((ec[ye == k] == k).mean()), 3) for k in range(4)])
    v = pd.read_csv(RAIZ / "data/evaluation/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv")
    vc = predecir_dir(a.cand, v.texto); af = v.tipo == "afectiva"
    n_af, n_in = int((vc[af] == 0).sum()), int((vc[~af] != 0).sum())
    R["d"] = dict(afectivas_ok=n_af, de=int(af.sum()), insultos_ok=n_in, de_i=int((~af).sum()))
    print(f"[d] vulgaridad afectiva: afectivas→No Tóxico {n_af}/{int(af.sum())} · insultos detectados {n_in}/{int((~af).sum())}")
    ok = dict(a=not (R["a"]["p"] < 0.05 and R["a"]["delta"] < 0), b=bc >= br - 2, c=lo2 > 0, d=(n_af >= 17 and n_in >= 16))
    print("\nCRITERIOS:", " · ".join(f"({k}) {'sí' if val else 'NO'}" for k, val in ok.items()), "->", "ADOPTAR" if all(ok.values()) else "NO ADOPTAR")
    R["decision"] = {k: bool(val) for k, val in ok.items()} | {"adoptar": bool(all(ok.values()))}
    Path(a.cand, "comparacion_candidato.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
