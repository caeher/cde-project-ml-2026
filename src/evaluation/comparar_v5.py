# -*- coding: utf-8 -*-
"""Compara v5 (hilos reales + casos difíciles) contra el modelo final (models/v3.0.0), mismo protocolo.

CRITERIOS DE ADOPCIÓN, fijados ANTES de ver resultados:
  (a) test oficial: SIN regresión significativa (McNemar pareado, p >= 0.05 si v5 baja).
      [Revisado el 11-oct-2026 por decisión de la persona responsable, ANTES de ver los resultados de peso 1.0:
       el criterio original exigía además ΔF1 >= -0.010. Con el original, la corrida de peso 3.0 ya había fallado
       (Δ -0.032, p = 0.011) y sigue fallando con el revisado, así que no se cambió para aprobar nada.];
  (b) batería de 144: no pierde más de 2 aciertos;
  (c) hilos reservados (nunca vistos, hilos completos): mejora de F1-macro con IC 95 % pareado que NO cruza el cero.
Se adopta solo si se cumplen (a), (b) y (c). Los casos probe (n pequeño) y la memorización son diagnóstico, no criterio.

Uso: python src/evaluation/comparar_v5.py --v5 runs/v5a --dataset data/history/v1.4.0-a --base models/v3.0.0
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_f1, ic_delta  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def mean_probs(run, nombre):
    return np.mean([np.load(f) for f in sorted(Path(run).glob(f"semilla_*/{nombre}.npy"))], 0)


def tokens(t, n=4):
    w = re.findall(r"\w+", unicodedata.normalize("NFKC", str(t)).lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def seccion(titulo, y, pb, pv, extra=""):
    m = mcnemar(pb == y, pv == y); lo, hi, _ = ic_delta(y, pb, pv)
    flo, fhi = ic_f1(y, pv)
    print(f"\n[{titulo}] n = {len(y)} {extra}")
    print(f"  F1-macro  base {f1m(y, pb):.4f}  v5 {f1m(y, pv):.4f}  Δ {f1m(y, pv) - f1m(y, pb):+.4f}  IC pareado [{lo:+.4f}, {hi:+.4f}]")
    print(f"  acierto   base {(pb == y).mean():.3f}  v5 {(pv == y).mean():.3f}   McNemar b/c {m['b']}/{m['c']}  p = {m['p_exacta']:.4f}")
    return dict(f1_base=f1m(y, pb), f1_v5=f1m(y, pv), delta=f1m(y, pv) - f1m(y, pb), ic_delta=[lo, hi],
                p=float(m["p_exacta"]), b=m["b"], c=m["c"], ic_v5=[float(flo), float(fhi)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v5", required=True); ap.add_argument("--dataset", required=True)
    ap.add_argument("--base", default="models/v3.0.0"); a = ap.parse_args()
    D = Path(a.dataset); R = {}
    te, adv = pd.read_csv(D / "test.csv"), pd.read_csv(D / "test_adversarial.csv")

    # (a) test oficial
    yt = te.label.values
    pb, pv = mean_probs(a.base, "probs_test").argmax(1), mean_probs(a.v5, "probs_test").argmax(1)
    R["test"] = seccion("test oficial", yt, pb, pv)
    for plat in sorted(te.Plataforma.dropna().unique()):
        mk = (te.Plataforma == plat).values
        print(f"    {plat:<9} base {f1m(yt[mk], pb[mk]):.4f}  v5 {f1m(yt[mk], pv[mk]):.4f}")

    # (b) batería
    ya = adv.label_esperado.values
    ab, av = mean_probs(a.base, "probs_adv").argmax(1), mean_probs(a.v5, "probs_adv").argmax(1)
    R["bateria"] = dict(base=int((ab == ya).sum()), v5=int((av == ya).sum()))
    print(f"\n[batería 144] base {R['bateria']['base']}  v5 {R['bateria']['v5']}")
    for g, idx in adv.groupby("grupo_de_prueba").groups.items():
        idx = np.asarray(list(idx)); print(f"    {g:<44} {int((ab[idx] == ya[idx]).sum()):>3} -> {int((av[idx] == ya[idx]).sum()):>3} / {len(idx)}")

    # (c) hilos reservados
    if (D / "hilos_reservados.csv").exists():
        h = pd.read_csv(D / "hilos_reservados.csv"); yh = h.label.values
        hb = np.load(RAIZ / "runs/final5_extra_hilos.npy").argmax(1); hv = mean_probs(a.v5, "probs_extra_hilos").argmax(1)
        R["hilos"] = seccion("hilos reservados", yh, hb, hv, f"({', '.join(sorted(h.hilo.unique()))})")
        for nm, m_ in [("No Tóxico", 0), ("Ofensivo", 1), ("Odio", 2), ("Amenazas", 3)]:
            s = yh == m_; print(f"    recall {nm:<10} n={int(s.sum()):<4} base {(hb[s] == m_).mean():.3f}  v5 {(hv[s] == m_).mean():.3f}")
        s = yh == 0; print(f"    FPR sobre No Tóxico      base {(hb[s] != 0).mean():.3f}  v5 {(hv[s] != 0).mean():.3f}")
        for hl in sorted(h.hilo.unique()):
            s = (h.hilo == hl).values; print(f"    hilo {hl:<12} F1 base {f1m(yh[s], hb[s]):.4f}  v5 {f1m(yh[s], hv[s]):.4f}")
        # diagnóstico de memorización: solape de 4-gramas entre lo añadido al train y los hilos reservados
        tr = pd.read_csv(D / "train.csv"); nuevo = tr[tr.origen.isin(["real_hilo", "caso_dificil"])]
        tr_g = set().union(*[tokens(t) for t in nuevo.texto_original]) if len(nuevo) else set()
        sol = np.array([bool(tokens(t) & tr_g) for t in h.texto_original])
        print(f"    solape de 4-gramas con lo añadido al train: {sol.mean():.3f} de los textos reservados "
              f"(acierto v5 con solape {(hv[sol] == yh[sol]).mean() if sol.any() else float('nan'):.3f}, sin solape {(hv[~sol] == yh[~sol]).mean():.3f})")
    # casos probe
    if (D / "casos_probe.csv").exists():
        c = pd.read_csv(D / "casos_probe.csv"); yc = c.label.values
        cb = np.load(RAIZ / "runs/final5_extra_probe.npy").argmax(1); cv = mean_probs(a.v5, "probs_extra_probe").argmax(1)
        R["probe"] = seccion("casos probe (pares mínimos no vistos)", yc, cb, cv)
        for g in sorted(c.grupo.unique()):
            s = (c.grupo == g).values; print(f"    {g:<22} n={int(s.sum()):<3} base {(cb[s] == yc[s]).mean():.2f}  v5 {(cv[s] == yc[s]).mean():.2f}")

    ok_a = not (R["test"]["p"] < 0.05 and R["test"]["delta"] < 0)
    ok_b = R["bateria"]["v5"] >= R["bateria"]["base"] - 2
    ok_c = "hilos" in R and R["hilos"]["ic_delta"][0] > 0
    print(f"\nCRITERIOS: (a) test sin regresión: {'sí' if ok_a else 'NO'} · (b) batería ≥ base−2: {'sí' if ok_b else 'NO'} · "
          f"(c) hilos reservados con IC>0: {'sí' if ok_c else 'NO'}  ->  {'ADOPTAR' if (ok_a and ok_b and ok_c) else 'NO ADOPTAR'}")
    R["decision"] = dict(a=bool(ok_a), b=bool(ok_b), c=bool(ok_c), adoptar=bool(ok_a and ok_b and ok_c))
    Path(a.v5, "comparacion_v5.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
