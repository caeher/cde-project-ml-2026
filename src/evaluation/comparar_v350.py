# -*- coding: utf-8 -*-
"""Ronda 3: compara un candidato contra la referencia v3.4.0 con los criterios fijados ANTES de entrenar
(docs/improvement/Plan_ronda3_amenazas_jerga.md). Una sola medición: banco congelado + test oficial + sonda afectiva.

Uso: python src/evaluation/comparar_v350.py <referencia> <candidato> [<candidato> ...] [--salida nombre]
     (nombres = carpetas de models/; con manifest.json se usa como ensamble)
Salida: reports/improvement/<salida>.md y .json (por defecto v350_candidatos)

Limitación declarada: la reserva `jerga_dev` del plan no se apartó al construir el dataset v1.9.0, así que el
criterio 2 se mide solo con el test oficial (n_jerga > 0).
"""
import json, sys
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402
from src.evaluation.comparar_fase3 import probs, temperatura  # noqa: E402
from src.evaluation.metrics import f1m, ic_f1, ic_delta, mcnemar  # noqa: E402


def f1_clase(y, p, c): return f1_score(y == c, p == c, zero_division=0)


def ic_delta_clase(y, pa, pb, c, n=5000, seed=42):
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y)); v.append(f1_clase(y[i], pb[i], c) - f1_clase(y[i], pa[i], c))
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def main():
    args = sys.argv[1:]; salida = "v350_candidatos"
    if "--salida" in args: k = args.index("--salida"); salida = args[k + 1]; args = args[:k] + args[k + 2:]
    ref, cands = args[0], args[1:]
    D, B = P.DATASET, P.FROZEN_BANK
    bk = pd.concat([pd.read_csv(B / f"{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]], ignore_index=True)
    yb = bk.label.values; te = pd.read_csv(D / "test.csv"); yt = te.label.values; va = pd.read_csv(D / "val.csv")
    pr = pd.read_csv(P.AFFECTIVE_PROBE); af = (pr.tipo == "afectiva").values; jt = te.n_jerga.fillna(0).values > 0
    R, PB = {}, {}
    for n in [ref] + cands:
        pb = probs(n, "bancoF", bk.texto_original.tolist()); pt = probs(n, "testF", te.texto_original.tolist())
        pv = probs(n, "valF", va.texto_original.tolist()); pp = probs(n, "probeF", pr.texto.tolist())
        p, q, a = pb.argmax(1), pt.argmax(1), pp.argmax(1); PB[n] = p; lo, hi = ic_f1(yb, p)
        R[n] = dict(f1_banco=f1m(yb, p), ic=[float(lo), float(hi)], recall=[float((p[yb == c] == c).mean()) for c in range(4)],
                    f1_amenazas=float(f1_clase(yb, p, 3)), fpr=float((p[yb == 0] != 0).mean()), f1_test=f1m(yt, q),
                    fpr_jerga_test=float((q[(yt == 0) & jt] != 0).mean()), n_nt_jerga=int(((yt == 0) & jt).sum()),
                    fpr_sin_jerga_test=float((q[(yt == 0) & ~jt] != 0).mean()),
                    afectivas=int((a[af] == 0).sum()), insultos=int((a[~af] != 0).sum()), T=temperatura(pv, va.label.values))
    L = [f"# Ronda 3: candidatos frente a {ref} (banco congelado n = {len(yb)}, test oficial n = {len(yt)})", "",
         "| Modelo | F1 banco [IC 95 %] | Rec. Odio | Rec. Amenazas | F1 Amenazas | FPR NT | Test F1 | FPR NT jerga (test) | Afect./Ins. | T |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in R.items():
        L.append(f"| {n} | {r['f1_banco']:.3f} [{r['ic'][0]:.3f}, {r['ic'][1]:.3f}] | {r['recall'][2]:.3f} | {r['recall'][3]:.3f} | {r['f1_amenazas']:.3f} | "
                 f"{r['fpr']:.3f} | {r['f1_test']:.3f} | {r['fpr_jerga_test']:.3f} (n={r['n_nt_jerga']}) | {r['afectivas']}/20 · {r['insultos']}/18 | {r['T']:.2f} |")
    L += ["", "## Criterios del plan (fijados antes de entrenar)", ""]
    r0 = R[ref]
    for n in cands:
        r = R[n]; lo_a, hi_a = ic_delta_clase(yb, PB[ref], PB[n], 3); lo, hi, _ = ic_delta(yb, PB[ref], PB[n]); m = mcnemar(PB[ref] == yb, PB[n] == yb)
        r.update(ic_delta_f1_amenazas=[lo_a, hi_a], ic_delta_f1=[lo, hi], mcnemar=m)
        ok = {"1a recall Amenazas ≥ 0.55": r["recall"][3] >= .55, "1b ΔF1 Amenazas IC > 0": lo_a > 0,
              "2 FPR NT con jerga (test) ≤ 0.24": r["fpr_jerga_test"] <= .24,
              "3a F1 banco no baja > 0.01": r["f1_banco"] >= r0["f1_banco"] - .01, "3b test oficial ≥ 0.83": r["f1_test"] >= .83,
              "3c FPR global ≤ 0.12": r["fpr"] <= .12, "3d afectivas ≥ 17 e insultos ≥ 16": r["afectivas"] >= 17 and r["insultos"] >= 16,
              "3e recall Odio no baja > 0.03": r["recall"][2] >= r0["recall"][2] - .03}
        r["criterios"] = ok
        L += [f"### {n}", f"ΔF1 banco {r['f1_banco'] - r0['f1_banco']:+.4f} IC [{lo:+.3f}, {hi:+.3f}] · McNemar b/c {m['b']}/{m['c']} p = {m['p_exacta']:.4f} · "
              f"ΔF1 Amenazas IC [{lo_a:+.3f}, {hi_a:+.3f}]", ""] + [f"- {'✔' if v else '✘'} {k}" for k, v in ok.items()] + \
             ["", f"**{'SE ADOPTA' if all(ok.values()) else 'NO se adopta'}** ({sum(ok.values())}/{len(ok)})", ""]
    L += ["Nota: la reserva `jerga_dev` no se apartó en el dataset v1.9.0; el criterio 2 usa solo el test oficial."]
    (P.REPORTS_IMPROVEMENT / f"{salida}.md").write_text("\n".join(L), encoding="utf-8")
    (P.REPORTS_IMPROVEMENT / f"{salida}.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float), encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
