# -*- coding: utf-8 -*-
"""Candidato v3.3.0-rc1 (v3.2.0-rc1 + 2 hilos ricos en Amenazas) frente a v3.2.0-rc1 (misma receta; solo cambian los datos).

CRITERIOS fijados ANTES de ver resultados:
  (a) test oficial: sin regresión significativa (McNemar pareado, p >= 0.05 si baja);
  (b) batería de 144: no pierde más de 2 aciertos;
  (c) hilo reservado militares_pandilleros (n=203, 107 Amenazas, nunca entrenado): F1 de la clase Amenazas mejora con IC 95 % pareado > 0;
  (d) vulgaridad afectiva: afectivas → No Tóxico >= 17/20 e insultos detectados >= 16/18;
  (e) sin costo en falsos positivos: FPR sobre No Tóxico (migrantes + externo 2 agrupados) no sube más de 0.03.
Uso: python src/evaluation/comparar_v330.py
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.combinar_modelos import probs_propio, cache  # noqa: E402
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m  # noqa: E402
from sklearn.metrics import f1_score

CAND = RAIZ / "models/v3.3.0-rc1"; D = RAIZ / "data/history/v1.6.0"


def mp(run, n): return np.mean([np.load(f) for f in sorted(Path(run).glob(f"semilla_*/{n}.npy"))], 0)


def f1_am(y, p): return f1_score(y == 3, p == 3, zero_division=0)


def boot_delta(y, a, b, fn, n=4000, seed=42):
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y)); v.append(fn(y[i], b[i]) - fn(y[i], a[i]))
    return np.percentile(v, [2.5, 97.5])


def main():
    te, adv = pd.read_csv(D / "test.csv"), pd.read_csv(D / "test_adversarial.csv"); y = te.label.values; R = {}
    pr, pc = mp("models/v3.2.0-rc1", "probs_test").argmax(1), mp(CAND, "probs_test").argmax(1)
    m = mcnemar(pr == y, pc == y); R["a"] = dict(ref=f1m(y, pr), cand=f1m(y, pc), p=float(m["p_exacta"]))
    print(f"[a] test oficial  ref {R['a']['ref']:.4f}  cand {R['a']['cand']:.4f}  McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.3f}")
    ya = adv.label_esperado.values; br, bc = int((mp("models/v3.2.0-rc1", "probs_adv").argmax(1) == ya).sum()), int((mp(CAND, "probs_adv").argmax(1) == ya).sum())
    R["b"] = dict(ref=br, cand=bc); print(f"[b] batería       ref {br}  cand {bc}")
    mil = pd.read_csv(D / "externo_militares.csv"); ym = mil.label.values
    rm = cache("v3.2.0-rc1__militares", lambda: probs_propio("models/v3.2.0-rc1", mil.texto_original.tolist())).argmax(1)
    cm_ = mp(CAND, "probs_extra_militares").argmax(1); v31 = cache("v3.1.0__militares", lambda: probs_propio("models/v3.1.0", mil.texto_original.tolist())).argmax(1)
    lo, hi = boot_delta(ym, rm, cm_, f1_am); mm = mcnemar(rm == ym, cm_ == ym)
    R["c"] = dict(f1_am_ref=f1_am(ym, rm), f1_am_cand=f1_am(ym, cm_), ic=[float(lo), float(hi)], rec_ref=float((rm[ym == 3] == 3).mean()), rec_cand=float((cm_[ym == 3] == 3).mean()))
    print(f"[c] militares n={len(ym)} (Amenazas {int((ym == 3).sum())})  F1-Amenazas ref {R['c']['f1_am_ref']:.3f} cand {R['c']['f1_am_cand']:.3f}  IC Δ [{lo:+.3f},{hi:+.3f}]")
    print(f"    recall Amenazas ref {R['c']['rec_ref']:.3f} cand {R['c']['rec_cand']:.3f} (v3.1.0 {float((v31[ym == 3] == 3).mean()):.3f}) | acierto ref {(rm == ym).mean():.3f} cand {(cm_ == ym).mean():.3f} (McNemar p={mm['p_exacta']:.3f})")
    v = pd.read_csv(RAIZ / "data/evaluation/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv")
    import app.api.main as M
    M._modelos.clear(); M.MODELOS = CAND; vc = np.array([M.predecir(t)["label"] for t in v.texto]); af = v.tipo == "afectiva"
    a_ok, i_ok = int((vc[af] == 0).sum()), int((vc[~af] != 0).sum()); R["d"] = dict(afectivas=a_ok, insultos=i_ok); print(f"[d] afectivas→NT {a_ok}/20 · insultos {i_ok}/18")
    fp = {}
    for nom, ruta in [("mig", D / "externo_migrantes.csv"), ("ext2", D / "externo_2.csv")]:
        d = pd.read_csv(ruta); yy = d.label.values; rr = cache(f"v3.2.0-rc1__{'mig' if nom == 'mig' else 'ext2'}", lambda: probs_propio("models/v3.2.0-rc1", d.texto_original.tolist())).argmax(1)
        cc = mp(CAND, "probs_extra_migrantes" if nom == "mig" else "probs_extra_externo2").argmax(1); fp[nom] = (int((rr[yy == 0] != 0).sum()), int((cc[yy == 0] != 0).sum()), int((yy == 0).sum()))
    fr, fc, nn = sum(v[0] for v in fp.values()), sum(v[1] for v in fp.values()), sum(v[2] for v in fp.values())
    R["e"] = dict(ref=fr / nn, cand=fc / nn); print(f"[e] FPR sobre No Tóxico (mig+ext2, n={nn}): ref {fr / nn:.3f} cand {fc / nn:.3f}")
    ok = dict(a=not (R["a"]["p"] < 0.05 and R["a"]["cand"] < R["a"]["ref"]), b=bc >= br - 2, c=lo > 0, d=(a_ok >= 17 and i_ok >= 16), e=(fc / nn - fr / nn) <= 0.03)
    print("\nCRITERIOS:", " · ".join(f"({k}) {'sí' if x else 'NO'}" for k, x in ok.items()), "->", "ADOPTAR" if all(ok.values()) else "NO ADOPTAR")
    R["decision"] = {k: bool(x) for k, x in ok.items()} | {"adoptar": bool(all(ok.values()))}
    (CAND / "comparacion_v330.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
