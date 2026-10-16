# -*- coding: utf-8 -*-
"""
Reentrenamiento de RoBERTuito con el dataset v4 (Etapa II + 4,074 reales de X, oct. 2026).

Reproduce la configuración final de la Etapa II (Optuna, 20 pruebas TPE):
    lr 5.73e-5 · batch 32 · 6 épocas · weight decay 0.0176 · warmup 0.0929
    peso sintéticos 0.75 · ponderación por clase · 3 semillas + voto blando

Uso en Colab (GPU T4 o superior, ~5 min por semilla):
    !pip install -q transformers datasets accelerate scikit-learn
    !python src/train/entrenar_v4.py --train data/dataset_v4/train.csv --out models/v4

Ablaciones recomendadas (mismo comando, cambia un flag):
    --peso_nuevos 0.0       # equivalente a NO usar los datos nuevos (línea base exacta)
    --peso_nuevos 0.5       # los datos de X pesan la mitad (protege Facebook)
    --excluir_fuera_sv      # quita las 230 filas sin señal salvadoreña
"""
import argparse, json, os, random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          Trainer, TrainingArguments, DataCollatorWithPadding)

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MODELO_BASE = "pysentimiento/robertuito-base-uncased"


def args_():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/dataset_v4/train.csv")
    ap.add_argument("--val", default="data/dataset_v4/val.csv")
    ap.add_argument("--test", default="data/dataset_v4/test.csv")
    ap.add_argument("--adv", default="data/dataset_v4/test_adversarial.csv")
    ap.add_argument("--out", default="models/v4")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1337, 2026])
    ap.add_argument("--lr", type=float, default=5.73e-5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epocas", type=int, default=6)
    ap.add_argument("--wd", type=float, default=0.0176)
    ap.add_argument("--warmup", type=float, default=0.0929)
    ap.add_argument("--max_length", type=int, default=128)
    ap.add_argument("--peso_sintetico", type=float, default=0.75)
    ap.add_argument("--peso_nuevos", type=float, default=1.0, help="peso de las filas origen=real_x_oct2026")
    ap.add_argument("--excluir_fuera_sv", action="store_true")
    return ap.parse_args()


def fijar_semilla(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def preparar(texto):
    # RoBERTuito es uncased: el texto debe llegar en minúsculas.
    # Si el repo v3 usaba pysentimiento.preprocess_tweet, reemplazar aquí por esa función.
    return str(texto).lower()


class DS(torch.utils.data.Dataset):
    def __init__(self, enc, labels, pesos=None):
        self.enc, self.labels, self.pesos = enc, labels, pesos

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        item = {k: v[i] for k, v in self.enc.items()}
        item["labels"] = int(self.labels[i])
        if self.pesos is not None:
            item["peso"] = float(self.pesos[i])
        return item


class Colador(DataCollatorWithPadding):
    def __call__(self, feats):
        pesos = [f.pop("peso") for f in feats] if "peso" in feats[0] else None
        b = super().__call__(feats)
        if pesos is not None:
            b["peso"] = torch.tensor(pesos, dtype=torch.float)
        return b


class TrainerPonderado(Trainer):
    def __init__(self, *a, pesos_clase=None, **k):
        super().__init__(*a, **k)
        self.pesos_clase = pesos_clase

    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        peso = inputs.pop("peso", None)
        labels = inputs.pop("labels")
        out = model(**inputs)
        w = self.pesos_clase.to(out.logits.device) if self.pesos_clase is not None else None
        perdida = nn.functional.cross_entropy(out.logits, labels, weight=w, reduction="none")
        if peso is not None:
            perdida = perdida * peso.to(perdida.device)
        perdida = perdida.mean()
        return (perdida, out) if return_outputs else perdida


def f1m(y, p):
    return f1_score(y, p, average="macro")


def bootstrap(y, p, n=2000, s=42):
    r = np.random.default_rng(s); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y)); v.append(f1m(y[i], p[i]))
    return [float(x) for x in np.percentile(v, [2.5, 97.5])]


def main():
    a = args_()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tr, va, te = pd.read_csv(a.train), pd.read_csv(a.val), pd.read_csv(a.test)
    adv = pd.read_csv(a.adv) if os.path.exists(a.adv) else None

    if a.excluir_fuera_sv and "fuera_de_sv" in tr.columns:
        tr = tr[~tr.fuera_de_sv.astype(str).str.lower().eq("true")]
    origen = tr.get("origen", pd.Series("real", index=tr.index)).astype(str)
    pesos = np.where(origen.str.startswith("sintetico"), a.peso_sintetico,
                     np.where(origen.eq("real_x_oct2026"), a.peso_nuevos, 1.0))
    keep = pesos > 0
    tr, pesos = tr[keep].reset_index(drop=True), pesos[keep]
    cnt = np.bincount(tr.label, minlength=4)
    pesos_clase = torch.tensor(len(tr) / (4 * cnt), dtype=torch.float)
    print(f"train efectivo: {len(tr)} filas | por clase {cnt.tolist()} | pesos clase {pesos_clase.numpy().round(4).tolist()}")

    tok = AutoTokenizer.from_pretrained(MODELO_BASE)
    enc = lambda s: tok([preparar(t) for t in s], truncation=True, max_length=a.max_length)
    d_tr = DS(enc(tr.texto_modelo), tr.label.values, pesos)
    d_va = DS(enc(va.texto_modelo), va.label.values)
    d_te = DS(enc(te.texto_modelo), te.label.values)
    d_adv = DS(enc(adv.texto_normalizado), adv.label_esperado.values) if adv is not None else None

    probs_te, probs_adv, por_semilla = [], [], {}
    for s in a.seeds:
        fijar_semilla(s)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODELO_BASE, num_labels=4, id2label=dict(enumerate(CLASES)), label2id={c: i for i, c in enumerate(CLASES)})
        ta = TrainingArguments(
            output_dir=str(out / f"tmp_s{s}"), learning_rate=a.lr, per_device_train_batch_size=a.batch,
            per_device_eval_batch_size=64, num_train_epochs=a.epocas, weight_decay=a.wd, warmup_ratio=a.warmup,
            eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
            metric_for_best_model="f1_macro", greater_is_better=True, save_total_limit=1,
            seed=s, fp16=torch.cuda.is_available(), report_to=[], remove_unused_columns=False, logging_steps=50)
        trn = TrainerPonderado(model=model, args=ta, train_dataset=d_tr, eval_dataset=d_va,
                               data_collator=Colador(tok), pesos_clase=pesos_clase,
                               compute_metrics=lambda e: {"f1_macro": f1m(e.label_ids, e.predictions.argmax(-1))})
        trn.train()
        pv = trn.predict(d_va).predictions
        pt = trn.predict(d_te).predictions
        sm = lambda x: torch.softmax(torch.tensor(x), -1).numpy()
        probs_te.append(sm(pt))
        if d_adv is not None:
            probs_adv.append(sm(trn.predict(d_adv).predictions))
        por_semilla[s] = {"f1_val": f1m(va.label.values, pv.argmax(-1)), "f1_test": f1m(te.label.values, pt.argmax(-1))}
        trn.save_model(str(out / f"semilla_{s}")); tok.save_pretrained(str(out / f"semilla_{s}"))
        print(f"semilla {s}: val {por_semilla[s]['f1_val']:.4f} · test {por_semilla[s]['f1_test']:.4f}")

    # --- Ensemble por voto blando, regla fijada de antemano: promedio de las tres ---
    y = te.label.values
    P = np.mean(probs_te, 0); pred = P.argmax(-1)
    res = {"config": vars(a), "train_efectivo": int(len(tr)), "por_semilla": por_semilla,
           "ensemble_f1_test": f1m(y, pred), "ensemble_ic95": bootstrap(y, pred),
           "ensemble_aciertos": int((pred == y).sum()),
           "f1_por_clase": dict(zip(CLASES, f1_score(y, pred, average=None).round(4).tolist())),
           "matriz_confusion": confusion_matrix(y, pred).tolist()}
    if "Plataforma" in te.columns:
        res["f1_por_plataforma"] = {p: f1m(y[(te.Plataforma == p).values], pred[(te.Plataforma == p).values])
                                    for p in te.Plataforma.dropna().unique()}
    if "n_jerga" in te.columns:
        nt = (y == 0)
        for nom, m in [("con_jerga", te.n_jerga.values > 0), ("sin_jerga", te.n_jerga.values == 0)]:
            res[f"fpr_no_toxico_{nom}"] = float((pred[nt & m] != 0).mean())
    if probs_adv:
        pa = np.mean(probs_adv, 0).argmax(-1)
        adv["pred"] = pa; adv["ok"] = pa == adv.label_esperado
        res["bateria_144"] = f"{int(adv.ok.sum())}/{len(adv)}"
        res["bateria_por_grupo"] = adv.groupby("grupo_de_prueba").ok.agg(["sum", "size"]).astype(int).to_dict("index")

    id_col = [c for c in te.columns if c.lower() == "id"][0]
    pd.DataFrame({"ID": te[id_col], "y_pred": pred}).to_csv(out / "preds_test.csv", index=False)
    np.save(out / "probs_test.npy", P)
    json.dump(res, open(out / "metricas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=float)
    print(classification_report(y, pred, target_names=CLASES, digits=4))
    print(json.dumps({k: res[k] for k in ["ensemble_f1_test", "ensemble_ic95", "f1_por_plataforma", "bateria_144"] if k in res},
                     ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
