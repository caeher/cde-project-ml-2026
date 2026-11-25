# -*- coding: utf-8 -*-
"""Candidato v3.4.0-rc1 (= v3.3.0-rc1 + hilos de Odio lgbt_bandera, lgbt_ultimahora, racismo_orgullo) frente a v3.3.0-rc1 (mismos datos menos esos hilos).
Reservado entero: xenofobia_federico (882 → 238; 94 Odio). Política vigente (docs/improvement/Estrategia_mejora.md): la batería de 144 es solo diagnóstico.

CRITERIOS fijados ANTES de ver resultados:
  (a) test oficial: sin regresión significativa (McNemar p >= 0.05 si el candidato baja);
  (b) hilo reservado xenofobia: F1 de la clase Odio mejora con IC 95 % pareado > 0;
  (c) vulgaridad afectiva: afectivas → No Tóxico >= 17/20 e insultos >= 16/18;
  (d) FPR sobre No Tóxico (migrantes + externo 2 + militares agrupados) no sube más de 0.03;
  (e) no se pierde lo ganado en Amenazas: recall de Amenazas en militares no baja más de 0.05."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.combinar_modelos import probs_propio, cache  # noqa: E402
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m  # noqa: E402
from sklearn.metrics import f1_score
CAND = RAIZ / "models/v3.4.0-rc1"; D = RAIZ / "data/history/v1.7.0"; REF = "v3.3.0-rc1"
def mp(r, n): return np.mean([np.load(f) for f in sorted(Path(r).glob(f"semilla_*/{n}.npy"))], 0)
def boot(y, a, b, fn, n=4000, seed=42):
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y)); v.append(fn(y[i], b[i]) - fn(y[i], a[i]))
    return np.percentile(v, [2.5, 97.5])
def main():
    R = {}; te = pd.read_csv(D / "test.csv"); y = te.label.values
    pr, pc = mp(f"models/{REF}", "probs_test").argmax(1), mp(CAND, "probs_test").argmax(1); m = mcnemar(pr == y, pc == y)
    R["a"] = dict(ref=f1m(y, pr), cand=f1m(y, pc), p=float(m["p_exacta"])); print(f"[a] test oficial  ref {R['a']['ref']:.4f} cand {R['a']['cand']:.4f}  McNemar b/c {m['b']}/{m['c']} p={m['p_exacta']:.3f}")
    xe = pd.read_csv(D / "externo_xenofobia.csv"); yx = xe.label.values
    rx = cache(f"{REF}__xenofobia", lambda: probs_propio(f"models/{REF}", xe.texto_original.tolist())).argmax(1); cx = mp(CAND, "probs_extra_xenofobia").argmax(1)
    f1o = lambda yy, pp: f1_score(yy == 2, pp == 2, zero_division=0); lo, hi = boot(yx, rx, cx, f1o)
    R["b"] = dict(f1_ref=f1o(yx, rx), f1_cand=f1o(yx, cx), ic=[float(lo), float(hi)], rec_ref=float((rx[yx == 2] == 2).mean()), rec_cand=float((cx[yx == 2] == 2).mean()))
    print(f"[b] xenofobia n={len(yx)} (Odio {int((yx == 2).sum())})  F1-Odio ref {R['b']['f1_ref']:.3f} cand {R['b']['f1_cand']:.3f}  IC Δ [{lo:+.3f},{hi:+.3f}] | recall Odio ref {R['b']['rec_ref']:.3f} cand {R['b']['rec_cand']:.3f} | acierto ref {(rx == yx).mean():.3f} cand {(cx == yx).mean():.3f}")
    import app.api.main as M
    v = pd.read_csv(RAIZ / "data/evaluation/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv"); M._modelos.clear(); M.MODELOS = CAND
    vc = np.array([M.predecir(t)["label"] for t in v.texto]); af = v.tipo == "afectiva"; a_ok, i_ok = int((vc[af] == 0).sum()), int((vc[~af] != 0).sum())
    R["c"] = dict(afectivas=a_ok, insultos=i_ok); print(f"[c] afectivas→NT {a_ok}/20 · insultos {i_ok}/18")
    fp = [0, 0, 0]; rm = rc = None
    for nom, f, ex in [("mig", "externo_migrantes.csv", "migrantes"), ("ext2", "externo_2.csv", "externo2"), ("mil", "externo_militares.csv", "militares")]:
        d = pd.read_csv(D / f); yy = d.label.values
        r_ = cache(f"{REF}__{nom if nom != 'mil' else 'militares'}", lambda d=d: probs_propio(f"models/{REF}", d.texto_original.tolist())).argmax(1); c_ = mp(CAND, f"probs_extra_{ex}").argmax(1)
        fp[0] += int((r_[yy == 0] != 0).sum()); fp[1] += int((c_[yy == 0] != 0).sum()); fp[2] += int((yy == 0).sum())
        if nom == "mil": rm, rc = float((r_[yy == 3] == 3).mean()), float((c_[yy == 3] == 3).mean())
    R["d"] = dict(ref=fp[0] / fp[2], cand=fp[1] / fp[2]); R["e"] = dict(ref=rm, cand=rc)
    print(f"[d] FPR sobre No Tóxico (n={fp[2]}): ref {fp[0] / fp[2]:.3f} cand {fp[1] / fp[2]:.3f}"); print(f"[e] recall Amenazas en militares: ref {rm:.3f} cand {rc:.3f}")
    ok = dict(a=not (R["a"]["p"] < 0.05 and R["a"]["cand"] < R["a"]["ref"]), b=lo > 0, c=(a_ok >= 17 and i_ok >= 16), d=(fp[1] - fp[0]) / fp[2] <= 0.03, e=(rc - rm) >= -0.05)
    print("\nCRITERIOS:", " · ".join(f"({k}) {'sí' if x else 'NO'}" for k, x in ok.items()), "->", "ADOPTAR" if all(ok.values()) else "NO ADOPTAR")
    R["decision"] = {k: bool(x) for k, x in ok.items()} | {"adoptar": bool(all(ok.values()))}; (CAND / "comparacion_v340.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))
if __name__ == "__main__": main()
