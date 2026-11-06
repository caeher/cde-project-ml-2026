# -*- coding: utf-8 -*-
"""Dataset v2.0.0: compara candidatos contra v3.4.0 con los criterios de docs/improvement/Plan_v2_particion_hilos.md (fijados antes de entrenar).
Test principal = test_hilos (1,975) + banco congelado (1,391). Temperatura ajustada en val_v2 = val oficial + val_hilos.
Uso: python src/evaluation/comparar_v2.py v3.4.0 candB_v2 v3.6.0-rc1-sel [--solo-banco profR3 v3.5.0-rc1-sel mbert-sv] [--salida nombre]
Salida: reports/improvement/<salida>.md y .json (por defecto v360_candidatos)"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import f1_score
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402
from src.evaluation.comparar_fase3 import probs, temperatura  # noqa: E402
from src.evaluation.metrics import f1m, ic_f1, ic_delta, mcnemar  # noqa: E402


def main():
    a = sys.argv[1:]; salida = "v360_candidatos"; solo = []
    if "--salida" in a: k = a.index("--salida"); salida = a[k + 1]; a = a[:k] + a[k + 2:]
    if "--solo-banco" in a: k = a.index("--solo-banco"); solo = a[k + 1:]; a = a[:k]
    ref, cands = a[0], a[1:]
    D, B = P.DATASET, P.FROZEN_BANK
    bk = pd.concat([pd.read_csv(B / f"{k}.csv").assign(conj=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]], ignore_index=True)
    th = pd.read_csv(D / "test_hilos.csv", encoding="utf-8-sig"); vh = pd.read_csv(D / "val_hilos.csv", encoding="utf-8-sig")
    te, va, pr = pd.read_csv(D / "test.csv"), pd.read_csv(D / "val.csv"), pd.read_csv(P.AFFECTIVE_PROBE); af = (pr.tipo == "afectiva").values
    yb, yh, yt = bk.label.values, th.label.values, te.label.values; yv2 = np.concatenate([va.label.values, vh.label.values])
    jerga = th.hilo.astype(str).str.startswith("busqueda_").values
    R, PP = {}, {}
    for n in [ref] + cands + solo:
        pb = probs(n, "bancoF", bk.texto_original.tolist()); pt = probs(n, "testF", te.texto_original.tolist()); pp = probs(n, "probeF", pr.texto.tolist())
        pv = np.vstack([probs(n, "valF", va.texto_original.tolist()), probs(n, "valHF", vh.texto_original.tolist())])
        r = dict(T=temperatura(pv, yv2), f1_banco=f1m(yb, pb.argmax(1)), f1_test_oficial=f1m(yt, pt.argmax(1)),
                 afectivas=int((pp.argmax(1)[af] == 0).sum()), insultos=int((pp.argmax(1)[~af] != 0).sum()), solo_banco=n in solo)
        if n not in solo:
            ph = probs(n, "testHF", th.texto_original.tolist()); y = np.concatenate([yh, yb]); p = np.vstack([ph, pb]).argmax(1); PP[n] = (y, p)
            lo, hi = ic_f1(y, p); q = ph.argmax(1)
            r.update(f1_principal=f1m(y, p), ic=[float(lo), float(hi)], recall=[float((p[y == c] == c).mean()) for c in range(4)],
                     fpr=float((p[y == 0] != 0).mean()), f1_test_hilos=f1m(yh, q),
                     fpr_jerga=float((q[(yh == 0) & jerga] != 0).mean()), n_jerga_nt=int(((yh == 0) & jerga).sum()))
        R[n] = r
    L = [f"# Dataset v2.0.0: candidatos frente a {ref}", "", f"Test principal = test_hilos (n = {len(th)}) + banco congelado (n = {len(bk)}). Temperatura en val_v2 (n = {len(yv2)}).", "",
         "| Modelo | F1 principal [IC 95 %] | Rec. NT / OF / OD / AM | FPR | F1 test_hilos | F1 banco | FPR jerga | Test oficial | Afect./Ins. | T |", "|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in R.items():
        if r["solo_banco"]: continue
        L.append(f"| {n} | {r['f1_principal']:.3f} [{r['ic'][0]:.3f}, {r['ic'][1]:.3f}] | {' / '.join(f'{x:.2f}' for x in r['recall'])} | {r['fpr']:.3f} | {r['f1_test_hilos']:.3f} | "
                 f"{r['f1_banco']:.3f} | {r['fpr_jerga']:.3f} (n={r['n_jerga_nt']}) | {r['f1_test_oficial']:.3f} | {r['afectivas']}/20 · {r['insultos']}/18 | {r['T']:.2f} |")
    if solo:
        L += ["", "Entrenados con v1.9.0 (vieron los hilos de test_hilos): solo banco congelado.", "", "| Modelo | F1 banco | Test oficial | Afect./Ins. |", "|---|---|---|---|"]
        L += [f"| {n} | {R[n]['f1_banco']:.3f} | {R[n]['f1_test_oficial']:.3f} | {R[n]['afectivas']}/20 · {R[n]['insultos']}/18 |" for n in solo]
    L += ["", "## Criterios (fijados antes de entrenar)", ""]; r0 = R[ref]; y0, p0 = PP[ref]
    for n in cands:
        r = R[n]; y, p = PP[n]; lo, hi, _ = ic_delta(y0, p0, p); m = mcnemar(p0 == y0, p == y)
        ok = {"1 ΔF1 principal IC > 0": lo > 0, "2 FPR no sube > 0.01": r["fpr"] <= r0["fpr"] + .01, "3 recall Amenazas ≥ 0.55": r["recall"][3] >= .55,
              "4 recall Odio no baja > 0.03": r["recall"][2] >= r0["recall"][2] - .03, "5 afectivas ≥ 17 e insultos ≥ 16": r["afectivas"] >= 17 and r["insultos"] >= 16,
              "6 test oficial ≥ 0.82": r["f1_test_oficial"] >= .82, "7 FPR jerga < referencia": r["fpr_jerga"] < r0["fpr_jerga"]}
        r.update(criterios=ok, ic_delta=[lo, hi], mcnemar=m)
        L += [f"### {n}", f"ΔF1 principal {r['f1_principal'] - r0['f1_principal']:+.4f} IC [{lo:+.3f}, {hi:+.3f}] · McNemar b/c {m['b']}/{m['c']} p = {m['p_exacta']:.4f}", ""]
        L += [f"- {'✔' if v else '✘'} {k}" for k, v in ok.items()] + ["", f"**{'SE ADOPTA' if all(ok.values()) else 'NO se adopta'}** ({sum(ok.values())}/7)", ""]
    (P.REPORTS_IMPROVEMENT / f"{salida}.md").write_text("\n".join(L), encoding="utf-8")
    (P.REPORTS_IMPROVEMENT / f"{salida}.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float), encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
