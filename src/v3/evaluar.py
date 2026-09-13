# -*- coding: utf-8 -*-
"""
Evaluación completa de un checkpoint V3.

Produce todo lo que la tesina necesita en un solo paso y sobre las MISMAS
particiones de siempre: test.csv (n=460) sin tocar, la batería adversarial de
144 y la sonda dirigida de 204 casos construida durante la auditoría.

La batería se normaliza desde su texto crudo con el normalizador vigente, no
desde la columna guardada: esa columna se generó con el normalizador anterior y
usarla mezclaría dos contratos de inferencia distintos.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import numpy as np, pandas as pd, torch
from sklearn.metrics import (f1_score, accuracy_score, confusion_matrix, log_loss,
                             precision_recall_fscore_support, matthews_corrcoef,
                             cohen_kappa_score)
from scipy.stats import binomtest
from transformers import AutoTokenizer, AutoModelForSequenceClassification

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MAX_LEN = 128


def leer(p):
    d = pd.read_csv(p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


def ece(p, y, bins=10):
    conf, pred = p.max(1), p.argmax(1); acc = (pred == y).astype(float)
    e, n = 0.0, len(y)
    for lo in np.linspace(0, 1, bins + 1)[:-1]:
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.sum(): e += m.sum() / n * abs(acc[m].mean() - conf[m].mean())
    return float(e)


def bootstrap_f1(y, yp, n=4000, seed=42):
    r = np.random.default_rng(seed); idx = np.arange(len(y)); out = []
    for _ in range(n):
        s = r.choice(idx, len(idx), replace=True)
        if len(np.unique(y[s])) < 2: continue
        out.append(f1_score(y[s], yp[s], average="macro", zero_division=0))
    out = np.array(out)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), float(out.mean())


@torch.no_grad()
def logits(textos, tok, mod, dev, bs=32):
    o = []
    for i in range(0, len(textos), bs):
        e = tok(textos[i:i+bs], return_tensors="pt", truncation=True,
                max_length=MAX_LEN, padding=True).to(dev)
        o.append(mod(**e).logits.float().cpu().numpy())
    return np.concatenate(o)


def evaluar(ruta: Path, alias: str, salida: Path) -> dict:
    salida.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(str(ruta))
    mod = AutoModelForSequenceClassification.from_pretrained(str(ruta)).eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); mod.to(dev)

    test = leer(RAIZ / "data/dataset_v3/test.csv")
    val = leer(RAIZ / "data/dataset_v3/val.csv")
    adv = leer(RAIZ / "data/dataset_v3/test_adversarial.csv")
    sonda = leer(RAIZ / "reports/v2_auditoria/sonda_predicciones.csv")

    R: dict = {"alias": alias, "ruta": str(ruta)}

    # ─── test y val ──────────────────────────────────────────────────────
    for nom, df in (("test", test), ("val", val)):
        L = logits(df.texto_modelo.astype(str).tolist(), tok, mod, dev)
        np.save(salida / f"logits_{alias}_{nom}.npy", L)
        y, yp, P = df.label.values, L.argmax(1), softmax(L)
        pr, rc, f1c, sp = precision_recall_fscore_support(y, yp, labels=range(4), zero_division=0)
        d = dict(n=len(y), f1_macro=float(f1_score(y, yp, average="macro", zero_division=0)),
                 accuracy=float(accuracy_score(y, yp)), aciertos=int((y == yp).sum()),
                 mcc=float(matthews_corrcoef(y, yp)),
                 qwk=float(cohen_kappa_score(y, yp, weights="quadratic")),
                 ece=ece(P, y), log_loss=float(log_loss(y, P, labels=list(range(4)))),
                 matriz=confusion_matrix(y, yp, labels=range(4)).tolist(),
                 por_clase={CLASES[i]: dict(precision=float(pr[i]), recall=float(rc[i]),
                                            f1=float(f1c[i]), soporte=int(sp[i])) for i in range(4)})
        if nom == "test":
            lo, hi, mu = bootstrap_f1(y, yp)
            d.update(ic_lo=lo, ic_hi=hi, ic_media=mu)
            pd.DataFrame({"ID": df.ID, "y_pred": yp}).to_csv(salida / f"preds_{alias}.csv", index=False)
        R[nom] = d

    # ─── cortes ──────────────────────────────────────────────────────────
    y = test.label.values; yp = np.load(salida / f"logits_{alias}_test.npy").argmax(1)
    R["cortes"] = {}
    for pl in ["X", "Facebook"]:
        k = (test.Plataforma == pl).values
        R["cortes"][f"plataforma_{pl}"] = dict(
            n=int(k.sum()), f1_macro=float(f1_score(y[k], yp[k], average="macro", zero_division=0)))
    for nom, k in (("con_jerga", (test.n_jerga > 0).values), ("sin_jerga", (test.n_jerga == 0).values)):
        sel = k & (y == 0)
        R["cortes"][f"fpr_{nom}"] = dict(n=int(sel.sum()), fpr=float((yp[sel] != 0).mean()))
    R["cortes"]["brecha_fpr_dialectal"] = (R["cortes"]["fpr_con_jerga"]["fpr"]
                                           - R["cortes"]["fpr_sin_jerga"]["fpr"])

    # ─── batería adversarial (normalizada con el normalizador vigente) ───
    txt = [normalizar(str(t)) for t in adv.texto]
    La = logits(txt, tok, mod, dev); np.save(salida / f"logits_{alias}_adv.npy", La)
    pa, ya = La.argmax(1), adv.label_esperado.values
    R["bateria"] = {"global": f"{int((pa == ya).sum())}/{len(ya)}",
                    "aciertos": int((pa == ya).sum()), "n": len(ya)}
    for g, sub in adv.groupby("grupo_de_prueba"):
        i = sub.index.values
        R["bateria"][g] = dict(n=len(i), aciertos=int((pa[i] == ya[i]).sum()))
    d_ = adv.grupo_de_prueba.str.startswith("D."); e_ = adv.grupo_de_prueba.str.startswith("E.")
    R["bateria"]["brecha_D_E"] = float((pa[d_.values] != 0).mean() - (pa[e_.values] != 0).mean())

    # ─── sonda dirigida de 204 casos ─────────────────────────────────────
    st = [normalizar(str(t)) for t in sonda.texto]
    Ls = logits(st, tok, mod, dev); np.save(salida / f"logits_{alias}_sonda.npy", Ls)
    ps, ys = Ls.argmax(1), sonda.esperado.values
    R["sonda"] = {"global": f"{int((ps == ys).sum())}/{len(ys)}",
                  "aciertos": int((ps == ys).sum()), "n": len(ys)}
    for f, sub in sonda.groupby("familia"):
        i = sub.index.values
        R["sonda"][f] = dict(n=len(i), aciertos=int((ps[i] == ys[i]).sum()))
    j = sonda.familia.str.startswith("7."); c = sonda.familia.str.startswith("8.")
    R["sonda"]["brecha_dialectal"] = float((ps[j.values] != 0).mean() - (ps[c.values] != 0).mean())

    # ─── McNemar contra las referencias de la entrega 2v ─────────────────
    R["mcnemar"] = {}
    for ref in ["xlmr_v1", "mbert_b2", "xlmr_mit"]:
        f = RAIZ / f"reports/v2_auditoria/logits_{ref}_test.npy"
        if not f.exists(): continue
        pr_ = np.load(f).argmax(1)
        a, b_ = (yp == y), (pr_ == y)
        B, C = int((a & ~b_).sum()), int((~a & b_).sum())
        p = binomtest(B, B + C, 0.5).pvalue if B + C else 1.0
        R["mcnemar"][ref] = dict(b_solo_v3=B, c_solo_ref=C, p=float(p),
                                 favorece=alias if B > C else (ref if C > B else "empate"))

    del mod; torch.cuda.empty_cache()
    (salida / f"evaluacion_{alias}.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    return R


def imprimir(R):
    t = R["test"]
    print(f"\n{'='*66}\n{R['alias']}\n{'='*66}")
    print(f"  F1-macro test  {t['f1_macro']:.4f}   IC95 [{t['ic_lo']:.4f}, {t['ic_hi']:.4f}]"
          f"   {'META CUMPLIDA' if t['ic_lo'] >= 0.80 else '(IC inferior < 0.80)'}")
    print(f"  Accuracy       {t['accuracy']:.4f}   ({t['aciertos']}/{t['n']})")
    print(f"  F1-macro val   {R['val']['f1_macro']:.4f}")
    print(f"  ECE {t['ece']:.4f}   MCC {t['mcc']:.4f}   QWK {t['qwk']:.4f}")
    print("\n  por clase:")
    for c in CLASES:
        v = t["por_clase"][c]
        print(f"    {c:20s} P={v['precision']:.4f} R={v['recall']:.4f} F1={v['f1']:.4f} n={v['soporte']}")
    co = R["cortes"]
    print(f"\n  X {co['plataforma_X']['f1_macro']:.4f} | Facebook {co['plataforma_Facebook']['f1_macro']:.4f}")
    print(f"  FPR jerga {co['fpr_con_jerga']['fpr']:.4f} (n={co['fpr_con_jerga']['n']}) | "
          f"sin jerga {co['fpr_sin_jerga']['fpr']:.4f} | brecha {co['brecha_fpr_dialectal']:+.4f}")
    print(f"\n  batería 144: {R['bateria']['global']}   brecha D-E {R['bateria']['brecha_D_E']:+.4f}")
    for g in sorted(k for k in R["bateria"] if k[0].isupper()):
        v = R["bateria"][g]; print(f"    {g:34s} {v['aciertos']:3d}/{v['n']}")
    print(f"\n  sonda 204: {R['sonda']['global']}   brecha dialectal {R['sonda']['brecha_dialectal']:+.4f}")
    for f in sorted(k for k in R["sonda"] if k[0].isdigit()):
        v = R["sonda"][f]; print(f"    {f:34s} {v['aciertos']:3d}/{v['n']}")
    print("\n  McNemar:")
    for r, v in R["mcnemar"].items():
        print(f"    vs {r:10s} b={v['b_solo_v3']:3d} c={v['c_solo_ref']:3d} p={v['p']:.4f} -> {v['favorece']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ruta"); ap.add_argument("alias")
    ap.add_argument("--salida", default=str(RAIZ / "reports/v3_resultados"))
    a = ap.parse_args()
    imprimir(evaluar(Path(a.ruta), a.alias, Path(a.salida)))
