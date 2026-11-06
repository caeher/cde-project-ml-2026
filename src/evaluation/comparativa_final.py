# -*- coding: utf-8 -*-
"""Comparativa final de todos los modelos del proyecto con varias métricas, desde las probabilidades en caché (runs/ext; sin GPU).
Fuente principal: banco congelado (n = 1,391; 4 hilos reales que ningún modelo vio). El test oficial (n = 460, solo Etapa I) se
reporta aparte y se marca cuando el modelo pudo verlo al entrenar. Uso: python src/evaluation/comparativa_final.py
Salida: reports/final/comparativa_modelos.{md,json,csv}"""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402
from src.evaluation.metrics import ic_f1, ic_delta, mcnemar  # noqa: E402

EXT = P.RUNS / "ext"
JERGA = re.compile(r"\bcerote|\bmaje\b|\bvergon|\bverga\b|\bputa\b|chucho|\bcipote|pupusa|\bbicho\b|puchica|\bchivo\b|\bchero\b|guanaco|a huevo|\bpisto\b", re.I)
# nombre: (componentes en caché, autor, técnica, test oficial visto al entrenar)
M = {
 "v3.0.0":          (["v3.0.0"], "Willian", "RoBERTuito, 5 semillas, datos Etapa II; cierre Etapa II", False),
 "v3.1.0":          (["v3.1.0"], "Willian", "v3.0.0 + 716 respuestas de hilos reales (etiquetas de Claude) + 88 casos difíciles", False),
 "v3.2.0":          (["v3.1.0", "v3.2.0-rc1"], "Willian", "Ensamble 10 modelos; rc1 con etiquetas por consenso de 3 anotadores", False),
 "v3.3.0":          (["v3.2.0-rc1", "v3.3.0-rc1"], "Willian", "Ensamble 10 modelos; + hilos ricos en Amenazas", False),
 "v3.4.0 (API)":    (["v3.4.0"], "Willian", "Optuna (CV por hilo) + destilación de ensamble de 6 a 1 RoBERTuito; dataset 1.8.0", False),
 "Profesor R3":     (["candB_r3"], "Willian", "Receta Optuna x 3 semillas; dataset 1.9.0 (ronda 3: +8,944 textos, Amenazas implícitas)", False),
 "v3.5.0-rc1":      (["v3.5.0-rc1-sel"], "Willian", "Profesor R3 destilado a 1 RoBERTuito (T 1, alfa 0.5)", False),
 "mBERT-SV":        (["mbert-sv"], "Cristian", "mBERT cased, fine-tuning continuado desde su v4; dataset 1.9.0; CE, 5 épocas, 1 semilla", False),
 "XLM-R v4":        (["xlmr-julio-v4"], "Julio", "XLM-R base; corpus del proyecto + Davidson et al. (inglés); split propio", True),
}
CL = ["No Tóxico", "Ofensivo", "Odio", "Amenazas"]

def carga(c, et):
    alt = {"bancoF": ["bancoF"], "testF": ["testF", "test"], "valF": ["valF", "val"], "probeF": ["probeF", "afec"]}[et]
    for a in alt:
        f = EXT / f"{c}__{a}.npy"
        if f.exists(): return np.load(f)
    raise FileNotFoundError(f"{c} {et}")
def probs(comp, et): return np.mean([carga(c, et) for c in comp], 0)
def temp(pv, y):
    z = np.log(np.clip(pv, 1e-12, 1))
    def nll(T):
        q = z / T; q = q - q.max(1, keepdims=True); return -(q - np.log(np.exp(q).sum(1, keepdims=True)))[np.arange(len(y)), y].mean()
    return float(minimize_scalar(nll, bounds=(0.5, 5), method="bounded").x)
def calib(p, T): z = np.log(np.clip(p, 1e-12, 1)) / T; q = np.exp(z - z.max(1, keepdims=True)); return q / q.sum(1, keepdims=True)
def ece(p, y, b=15):
    c, k = p.max(1), p.argmax(1); e = 0
    for lo in np.linspace(0, 1, b + 1)[:-1]:
        m = (c > lo) & (c <= lo + 1 / b)
        if m.any(): e += m.mean() * abs((k[m] == y[m]).mean() - c[m].mean())
    return float(e)

D, B = P.DATASET, P.FROZEN_BANK
bk = pd.concat([pd.read_csv(B / f"{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]], ignore_index=True)
te, va, pr = pd.read_csv(D / "test.csv"), pd.read_csv(D / "val.csv"), pd.read_csv(P.AFFECTIVE_PROBE)
yb, yt, yv = bk.label.values, te.label.values, va.label.values; af = (pr.tipo == "afectiva").values
jb = bk.texto_original.astype(str).str.contains(JERGA).values; jt = te.n_jerga.fillna(0).values > 0
R, PRED = {}, {}
for n, (comp, autor, tec, fuga) in M.items():
    pb, pt, pv, pp = (probs(comp, e) for e in ["bancoF", "testF", "valF", "probeF"])
    T = temp(pv, yv); pbc = calib(pb, T); p = pb.argmax(1); q = pt.argmax(1); a = pp.argmax(1); PRED[n] = p
    pr_, rc_, f1_, _ = precision_recall_fscore_support(yb, p, labels=[0, 1, 2, 3], zero_division=0); lo, hi = ic_f1(yb, p)
    tox = (yb != 0).astype(int)
    R[n] = dict(autor=autor, tecnica=tec, n_modelos=sum(len(list((P.MODELS / c).glob("semilla_*/modelo"))) or 1 for c in comp),
        f1_banco=float(f1_score(yb, p, average="macro")), ic=[float(lo), float(hi)], acierto=float((p == yb).mean()),
        precision=pr_.tolist(), recall=rc_.tolist(), f1=f1_.tolist(),
        fpr=float((p[yb == 0] != 0).mean()), fnr_toxico=float((p[yb != 0] == 0).mean()),
        auroc_toxico=float(roc_auc_score(tox, 1 - pb[:, 0])), ece=ece(pbc, yb), T=T,
        por_banco={k: dict(f1=float(f1_score(yb[m], p[m], average="macro", labels=[0, 1, 2, 3], zero_division=0)), acierto=float((p[m] == yb[m]).mean()))
                   for k in bk.banco.unique() for m in [bk.banco.values == k]},
        fpr_jerga_banco=float((p[(yb == 0) & jb] != 0).mean()), fpr_sin_jerga_banco=float((p[(yb == 0) & ~jb] != 0).mean()),
        fpr_jerga_test=float((q[(yt == 0) & jt] != 0).mean()),
        f1_test=float(f1_score(yt, q, average="macro")), test_contaminado=fuga,
        f1_test_X=float(f1_score(yt[te.Plataforma == "X"], q[te.Plataforma == "X"], average="macro")),
        f1_test_FB=float(f1_score(yt[te.Plataforma == "Facebook"], q[te.Plataforma == "Facebook"], average="macro")),
        afectivas=int((a[af] == 0).sum()), insultos=int((a[~af] != 0).sum()))
ref = "v3.4.0 (API)"
for n in M:
    if n == ref: continue
    lo, hi, _ = ic_delta(yb, PRED[ref], PRED[n]); m = mcnemar(PRED[ref] == yb, PRED[n] == yb)
    R[n]["vs_api"] = dict(delta_f1=R[n]["f1_banco"] - R[ref]["f1_banco"], ic=[lo, hi], mcnemar_b=m["b"], mcnemar_c=m["c"], p=m["p_exacta"])
O = RAIZ / "reports/final"; O.mkdir(parents=True, exist_ok=True)
(O / "comparativa_modelos.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
rows = [{"modelo": n, "autor": r["autor"], "f1_banco": r["f1_banco"], "ic_lo": r["ic"][0], "ic_hi": r["ic"][1], "acierto": r["acierto"],
         **{f"recall_{c}": r["recall"][i] for i, c in enumerate(CL)}, **{f"precision_{c}": r["precision"][i] for i, c in enumerate(CL)},
         **{f"f1_{c}": r["f1"][i] for i, c in enumerate(CL)}, "fpr": r["fpr"], "fnr_toxico": r["fnr_toxico"], "auroc_toxico": r["auroc_toxico"],
         "ece": r["ece"], "fpr_jerga_banco": r["fpr_jerga_banco"], "fpr_jerga_test": r["fpr_jerga_test"], "f1_test": r["f1_test"],
         "test_contaminado": r["test_contaminado"], "afectivas": r["afectivas"], "insultos": r["insultos"]} for n, r in R.items()]
pd.DataFrame(rows).to_csv(O / "comparativa_modelos.csv", index=False, encoding="utf-8")
print(pd.DataFrame(rows).set_index("modelo")[["f1_banco", "ic_lo", "ic_hi", "recall_Odio", "recall_Amenazas", "fpr", "fnr_toxico", "auroc_toxico", "ece", "fpr_jerga_banco", "f1_test", "afectivas", "insultos"]].round(3).to_string())
for n, r in R.items():
    print(n, {k: round(v["f1"], 3) for k, v in r["por_banco"].items()}, "X/FB", round(r["f1_test_X"], 3), round(r["f1_test_FB"], 3), r.get("vs_api", ""))
print("jerga banco n NT:", int(((yb == 0) & jb).sum()), "| test n NT jerga:", int(((yt == 0) & jt).sum()))
