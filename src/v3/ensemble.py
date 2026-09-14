# -*- coding: utf-8 -*-
"""
Ensemble por voto blando (promedio de probabilidades).

Se combinan modelos que difieren en algo real —semilla de inicialización o
corpus de preentrenamiento— porque promediar réplicas idénticas no reduce nada.
La selección de la combinación se hace SOBRE VALIDACIÓN; el test solo se toca
una vez, al final, con la combinación ya elegida.
"""
import json, sys
from itertools import combinations
from pathlib import Path

import numpy as np, pandas as pd, torch
from sklearn.metrics import f1_score, accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

SALIDA = RAIZ / "reports/v3_resultados"
# Solo modelos entrenados sobre el corpus corregido. Se excluye a propósito el
# TwitterXLM-R sobre B2: aunque mejoraba el F1 del conjunto, arrastra el atajo
# sintáctico «te voy a X» (14 falsos positivos de 24 en la sonda de
# construcción) y lo reintroducía en el promedio. Un miembro con un defecto
# conocido contamina el ensemble aunque suba la métrica agregada.
MIEMBROS = {
    "roberTuito_s42":   RAIZ / "models/v3/final_s42",
    "roberTuito_s1337": RAIZ / "models/v3/final_s1337",
    "roberTuito_s2026": RAIZ / "models/v3/final_s2026",
}


def leer(p):
    d = pd.read_csv(p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


@torch.no_grad()
def probs(ruta, textos, bs=32):
    tok = AutoTokenizer.from_pretrained(str(ruta))
    mod = AutoModelForSequenceClassification.from_pretrained(str(ruta)).eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); mod.to(dev)
    o = []
    for i in range(0, len(textos), bs):
        e = tok(textos[i:i+bs], return_tensors="pt", truncation=True,
                max_length=128, padding=True).to(dev)
        o.append(mod(**e).logits.float().cpu().numpy())
    del mod; torch.cuda.empty_cache()
    return softmax(np.concatenate(o))


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    val = leer(RAIZ / "data/dataset_v3/val.csv")
    test = leer(RAIZ / "data/dataset_v3/test.csv")
    adv = leer(RAIZ / "data/dataset_v3/test_adversarial.csv")
    sonda = leer(RAIZ / "reports/v2_auditoria/sonda_predicciones.csv")

    conj = {
        "val": (val.texto_modelo.astype(str).tolist(), val.label.values),
        "test": (test.texto_modelo.astype(str).tolist(), test.label.values),
        "adv": ([normalizar(str(t)) for t in adv.texto], adv.label_esperado.values),
        "sonda": ([normalizar(str(t)) for t in sonda.texto], sonda.esperado.values),
    }

    P = {}
    for nombre, ruta in MIEMBROS.items():
        if not ruta.exists():
            print(f"  [falta] {nombre}: {ruta}"); continue
        P[nombre] = {c: probs(ruta, tx) for c, (tx, _) in conj.items()}
        f1 = f1_score(conj["val"][1], P[nombre]["val"].argmax(1), average="macro", zero_division=0)
        print(f"  {nombre:18s} val F1 = {f1:.4f}", flush=True)

    # ── selección de la combinación sobre VALIDACIÓN ────────────────────
    nombres = list(P)
    print("\ncombinaciones (selección sobre val, el test no participa):")
    tabla = []
    for k in range(2, len(nombres) + 1):
        for combo in combinations(nombres, k):
            m = np.mean([P[n]["val"] for n in combo], axis=0)
            f1 = f1_score(conj["val"][1], m.argmax(1), average="macro", zero_division=0)
            tabla.append((f1, combo))
            print(f"  {f1:.4f}  {' + '.join(combo)}")
    # Regla de selección, fijada antes de mirar el test: se usan TODOS los
    # miembros, sin elegir. Cualquier criterio de selección —incluso sobre
    # validación— reintroduce el sesgo de escoger la combinación afortunada,
    # y con tres semillas el promedio completo es la opción menos sobreajustada.
    mejor = tuple(nombres)
    mejor_f1 = f1_score(conj["val"][1],
                        np.mean([P[n]["val"] for n in mejor], axis=0).argmax(1),
                        average="macro", zero_division=0)
    tabla.sort(reverse=True)

    indiv = max((f1_score(conj["val"][1], P[n]["val"].argmax(1), average="macro",
                          zero_division=0), n) for n in nombres)
    print(f"\nmejor individual  {indiv[0]:.4f}  ({indiv[1]})")
    print(f"mejor ensemble    {mejor_f1:.4f}  ({' + '.join(mejor)})")

    # ── evaluación final, una sola vez ──────────────────────────────────
    R = {"miembros": list(mejor), "val_f1_macro": float(mejor_f1),
         "mejor_individual": {"modelo": indiv[1], "val_f1_macro": float(indiv[0])},
         "todas_las_combinaciones": [{"f1_val": float(f), "miembros": list(c)} for f, c in tabla]}

    for c in ["test", "adv", "sonda"]:
        m = np.mean([P[n][c] for n in mejor], axis=0)
        y, yp = conj[c][1], m.argmax(1)
        R[c] = {"f1_macro": float(f1_score(y, yp, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(y, yp)),
                "aciertos": int((y == yp).sum()), "n": int(len(y))}
        if c == "test":
            np.save(SALIDA / "probs_ensemble_test.npy", m)
            rng = np.random.default_rng(42); idx = np.arange(len(y)); b = []
            for _ in range(4000):
                s = rng.choice(idx, len(idx), replace=True)
                if len(np.unique(y[s])) < 2: continue
                b.append(f1_score(y[s], yp[s], average="macro", zero_division=0))
            R[c]["ic_lo"], R[c]["ic_hi"] = float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))
            pd.DataFrame({"ID": test.ID, "y_pred": yp}).to_csv(SALIDA / "preds_ensemble.csv", index=False)

    (SALIDA / "ensemble.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"\n{'='*60}\nENSEMBLE FINAL: {' + '.join(mejor)}")
    print(f"  test  F1-macro {R['test']['f1_macro']:.4f}  "
          f"IC95 [{R['test']['ic_lo']:.4f}, {R['test']['ic_hi']:.4f}]  "
          f"acc {R['test']['accuracy']:.4f} ({R['test']['aciertos']}/{R['test']['n']})")
    print(f"  batería 144   {R['adv']['aciertos']}/{R['adv']['n']}")
    print(f"  sonda 204     {R['sonda']['aciertos']}/{R['sonda']['n']}")


if __name__ == "__main__":
    main()
