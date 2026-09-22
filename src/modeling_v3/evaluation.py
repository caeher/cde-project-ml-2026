# -*- coding: utf-8 -*-
"""Evaluación de checkpoints V3 sobre test, val y batería adversarial."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import binomtest
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_fscore_support,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from modeling_v3.constants import CLASES, DEFAULT_SEED, MAX_LEN, TEXT_COLUMN
from modeling_v3.data import leer_csv
from modeling_v3.device import require_cuda
from modeling_v3.normalization import normalizar
from modeling_v3.paths import default_data_dir


def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = p.max(1), p.argmax(1)
    acc = (pred == y).astype(float)
    err, n = 0.0, len(y)
    for lo in np.linspace(0, 1, bins + 1)[:-1]:
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.sum():
            err += m.sum() / n * abs(acc[m].mean() - conf[m].mean())
    return float(err)


def bootstrap_f1(y, yp, n: int = 4000, seed: int = DEFAULT_SEED):
    r = np.random.default_rng(seed)
    idx = np.arange(len(y))
    out = []
    for _ in range(n):
        s = r.choice(idx, len(idx), replace=True)
        if len(np.unique(y[s])) < 2:
            continue
        out.append(f1_score(y[s], yp[s], average="macro", zero_division=0))
    out_arr = np.array(out)
    return (
        float(np.percentile(out_arr, 2.5)),
        float(np.percentile(out_arr, 97.5)),
        float(out_arr.mean()),
    )


@torch.no_grad()
def logits_batch(textos, tok, mod, dev, bs: int = 32) -> np.ndarray:
    chunks = []
    for i in range(0, len(textos), bs):
        e = tok(
            textos[i : i + bs],
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LEN,
            padding=True,
        ).to(dev)
        chunks.append(mod(**e).logits.float().cpu().numpy())
    return np.concatenate(chunks)


def evaluar(
    ruta: Path,
    alias: str,
    salida: Path,
    *,
    data_dir: Path | None = None,
    sonda_csv: Path | None = None,
    referencia_logits_dir: Path | None = None,
    bootstrap_samples: int = 4000,
) -> dict:
    salida.mkdir(parents=True, exist_ok=True)
    data_root = data_dir if data_dir is not None else default_data_dir()

    tok = AutoTokenizer.from_pretrained(str(ruta))
    mod = AutoModelForSequenceClassification.from_pretrained(str(ruta)).eval()
    dev = require_cuda()
    mod.to(dev)

    test = leer_csv(data_root / "test.csv")
    val = leer_csv(data_root / "val.csv")
    adv_path = data_root / "test_adversarial.csv"
    adv = leer_csv(adv_path) if adv_path.is_file() else None

    resultado: dict = {"alias": alias, "ruta": str(ruta)}

    for nom, df in (("test", test), ("val", val)):
        L = logits_batch(df[TEXT_COLUMN].astype(str).tolist(), tok, mod, dev)
        np.save(salida / f"logits_{alias}_{nom}.npy", L)
        y, yp, p = df.label.values, L.argmax(1), softmax(L)
        pr, rc, f1c, sp = precision_recall_fscore_support(
            y, yp, labels=range(4), zero_division=0
        )
        bloque = {
            "n": len(y),
            "f1_macro": float(f1_score(y, yp, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y, yp)),
            "aciertos": int((y == yp).sum()),
            "mcc": float(matthews_corrcoef(y, yp)),
            "qwk": float(cohen_kappa_score(y, yp, weights="quadratic")),
            "ece": ece(p, y),
            "log_loss": float(log_loss(y, p, labels=list(range(4)))),
            "matriz": confusion_matrix(y, yp, labels=range(4)).tolist(),
            "por_clase": {
                CLASES[i]: {
                    "precision": float(pr[i]),
                    "recall": float(rc[i]),
                    "f1": float(f1c[i]),
                    "soporte": int(sp[i]),
                }
                for i in range(4)
            },
        }
        if nom == "test":
            lo, hi, mu = bootstrap_f1(y, yp, n=bootstrap_samples)
            bloque.update(ic_lo=lo, ic_hi=hi, ic_media=mu)
            if "ID" in df.columns:
                pd.DataFrame({"ID": df.ID, "y_pred": yp}).to_csv(
                    salida / f"preds_{alias}.csv", index=False
                )
        resultado[nom] = bloque

    y = test.label.values
    yp = np.load(salida / f"logits_{alias}_test.npy").argmax(1)
    resultado["cortes"] = {}
    if "Plataforma" in test.columns:
        for pl in ["X", "Facebook"]:
            k = (test.Plataforma == pl).values
            resultado["cortes"][f"plataforma_{pl}"] = {
                "n": int(k.sum()),
                "f1_macro": float(f1_score(y[k], yp[k], average="macro", zero_division=0)),
            }
    if "n_jerga" in test.columns:
        for nom, k in (
            ("con_jerga", (test.n_jerga > 0).values),
            ("sin_jerga", (test.n_jerga == 0).values),
        ):
            sel = k & (y == 0)
            resultado["cortes"][f"fpr_{nom}"] = {
                "n": int(sel.sum()),
                "fpr": float((yp[sel] != 0).mean()) if sel.sum() else 0.0,
            }
        if "fpr_con_jerga" in resultado["cortes"] and "fpr_sin_jerga" in resultado["cortes"]:
            resultado["cortes"]["brecha_fpr_dialectal"] = (
                resultado["cortes"]["fpr_con_jerga"]["fpr"]
                - resultado["cortes"]["fpr_sin_jerga"]["fpr"]
            )

    if adv is not None and "texto" in adv.columns and "label_esperado" in adv.columns:
        txt = [normalizar(str(t)) for t in adv.texto]
        la = logits_batch(txt, tok, mod, dev)
        np.save(salida / f"logits_{alias}_adv.npy", la)
        pa, ya = la.argmax(1), adv.label_esperado.values
        resultado["bateria"] = {
            "global": f"{int((pa == ya).sum())}/{len(ya)}",
            "aciertos": int((pa == ya).sum()),
            "n": len(ya),
        }
        if "grupo_de_prueba" in adv.columns:
            for g, sub in adv.groupby("grupo_de_prueba"):
                i = sub.index.values
                resultado["bateria"][g] = {
                    "n": len(i),
                    "aciertos": int((pa[i] == ya[i]).sum()),
                }

    if sonda_csv is not None and sonda_csv.is_file():
        sonda = leer_csv(sonda_csv)
        if "texto" in sonda.columns and "esperado" in sonda.columns:
            st = [normalizar(str(t)) for t in sonda.texto]
            ls = logits_batch(st, tok, mod, dev)
            np.save(salida / f"logits_{alias}_sonda.npy", ls)
            ps, ys = ls.argmax(1), sonda.esperado.values
            resultado["sonda"] = {
                "global": f"{int((ps == ys).sum())}/{len(ys)}",
                "aciertos": int((ps == ys).sum()),
                "n": len(ys),
            }

    if referencia_logits_dir is not None:
        resultado["mcnemar"] = {}
        for ref in ["xlmr_v1", "mbert_b2", "xlmr_mit"]:
            f = referencia_logits_dir / f"logits_{ref}_test.npy"
            if not f.is_file():
                continue
            pr_ = np.load(f).argmax(1)
            a, b_ = (yp == y), (pr_ == y)
            b_cnt, c_cnt = int((a & ~b_).sum()), int((~a & b_).sum())
            pval = binomtest(b_cnt, b_cnt + c_cnt, 0.5).pvalue if b_cnt + c_cnt else 1.0
            resultado["mcnemar"][ref] = {
                "b_solo_v3": b_cnt,
                "c_solo_ref": c_cnt,
                "p": float(pval),
                "favorece": alias if b_cnt > c_cnt else (ref if c_cnt > b_cnt else "empate"),
            }

    del mod
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    out_json = salida / f"evaluacion_{alias}.json"
    out_json.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    return resultado
