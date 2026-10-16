# -*- coding: utf-8 -*-
"""Fase 3/4 del plan: tabla comparable de candidatos (A, B, C = A+B, estudiante destilado) frente a la línea base v3.3.0.
UNA sola medición sobre el banco congelado + test oficial + sonda de vulgaridad afectiva. La selección entre candidatos la fija la CV por hilo
(reports/optuna_cv_hilo.json: referencia = receta A, mejor = receta B); este script solo informa y comprueba las metas.

Metas del plan: recall Odio ≥ 0.65 · recall Amenazas ≥ 0.60 · FPR ≤ 0.12 · F1-macro banco ≥ 0.70 · test oficial ≥ 0.83 · afectivas ≥ 17/20 e insultos ≥ 16/18.
Uso: python src/evaluation/comparar_fase3.py v3.3.0 candA candB candC [student ...]   (nombres = carpetas de models/; si hay manifest.json se usa como ensamble)
Salida: reports/fase3_candidatos.md y .json
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.combinar_modelos import probs_propio, cache  # noqa: E402
from src.evaluation.comparar_modelos import mcnemar  # noqa: E402
from src.evaluation.comparar_v4 import f1m, ic_f1, ic_delta  # noqa: E402

D = RAIZ / "data/dataset_final"; B = RAIZ / "data/banco_congelado"


def probs(nombre, etiqueta, textos):
    ruta = RAIZ / "models" / nombre; man = ruta / "manifest.json"
    if man.exists():
        comp = json.loads(man.read_text(encoding="utf-8"))["componentes"]
        return np.mean([cache(f"{c}__{etiqueta}", lambda c=c: probs_propio(f"models/{c}", textos)) for c in comp], 0)
    return cache(f"{nombre}__{etiqueta}", lambda: probs_propio(f"models/{nombre}", textos))


def temperatura(p_val, y):
    z = np.log(np.clip(p_val, 1e-12, 1))
    def nll(T):
        q = z / T; q = q - q.max(1, keepdims=True); lp = q - np.log(np.exp(q).sum(1, keepdims=True)); return -lp[np.arange(len(y)), y].mean()
    return float(minimize_scalar(nll, bounds=(0.5, 5), method="bounded").x)


def main():
    nombres = sys.argv[1:] or ["v3.3.0", "candA"]
    bk = pd.concat([pd.read_csv(B / f"{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]], ignore_index=True)
    yb, tb = bk.label.values, bk.texto_original.tolist(); te = pd.read_csv(D / "test.csv"); yt = te.label.values; va = pd.read_csv(D / "val.csv")
    pr = pd.read_csv(RAIZ / "data/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv"); af = (pr.tipo == "afectiva").values
    R, PRED = {}, {}
    for n in nombres:
        pb = probs(n, "bancoF", tb); pt = probs(n, "testF", te.texto_original.tolist()); pv = probs(n, "valF", va.texto_original.tolist()); pp = probs(n, "probeF", pr.texto.tolist())
        T = temperatura(pv, va.label.values); p = pb.argmax(1); PRED[n] = p; lo, hi = ic_f1(yb, p); pa = pp.argmax(1)
        R[n] = dict(f1_banco=f1m(yb, p), ic=[lo, hi], acierto=float((p == yb).mean()), recall=[float((p[yb == c] == c).mean()) for c in range(4)], fpr=float((p[yb == 0] != 0).mean()),
                    f1_test=f1m(yt, pt.argmax(1)), afectivas=int((pa[af] == 0).sum()), insultos=int((pa[~af] != 0).sum()), T=T, n_modelos=len(list((RAIZ / "models" / n).glob("semilla_*/modelo"))) or None)
    base = nombres[0]; L = ["# Candidatos frente a la línea base (banco congelado n = %d)" % len(yb), "",
                            "| Modelo | F1-macro [IC 95 %] | Recall Odio | Recall Amenazas | Recall Ofensivo | FPR (NT) | Test oficial F1 | Afectivas / Insultos | T |", "|---|---|---|---|---|---|---|---|---|"]
    for n in nombres:
        r = R[n]; L.append(f"| {n} | {r['f1_banco']:.3f} [{r['ic'][0]:.3f}, {r['ic'][1]:.3f}] | {r['recall'][2]:.3f} | {r['recall'][3]:.3f} | {r['recall'][1]:.3f} | {r['fpr']:.3f} | {r['f1_test']:.3f} | {r['afectivas']}/20 · {r['insultos']}/18 | {r['T']:.2f} |")
    L += ["", f"Pareado contra {base} (banco):", ""]
    for n in nombres[1:]:
        m = mcnemar(PRED[base] == yb, PRED[n] == yb); lo, hi, _ = ic_delta(yb, PRED[base], PRED[n])
        L.append(f"- {n}: ΔF1 {R[n]['f1_banco'] - R[base]['f1_banco']:+.4f} IC [{lo:+.3f}, {hi:+.3f}] · McNemar b/c {m['b']}/{m['c']} p = {m['p_exacta']:.4f}")
    L += ["", "Metas (recall Odio ≥ 0.65, Amenazas ≥ 0.60, FPR ≤ 0.12, F1 banco ≥ 0.70, test ≥ 0.83, afectivas ≥ 17, insultos ≥ 16):", ""]
    for n in nombres:
        r = R[n]; ok = {"Odio": r["recall"][2] >= .65, "Amenazas": r["recall"][3] >= .60, "FPR": r["fpr"] <= .12, "F1": r["f1_banco"] >= .70, "test": r["f1_test"] >= .83, "afect": r["afectivas"] >= 17, "insultos": r["insultos"] >= 16}
        L.append(f"- {n}: " + " · ".join(f"{k} {'✔' if v else '✘'}" for k, v in ok.items()) + f"  ({sum(ok.values())}/7)")
    (RAIZ / "reports/fase3_candidatos.md").write_text("\n".join(L), encoding="utf-8")
    (RAIZ / "reports/fase3_candidatos.json").write_text(json.dumps(R, indent=2, ensure_ascii=False), encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
