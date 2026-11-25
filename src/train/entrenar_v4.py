# -*- coding: utf-8 -*-
"""
Reentrenamiento de RoBERTuito con el dataset v4 (Etapa II + reales de X, oct. 2026).

Réplica fiel de la receta de la Etapa II (repo v3: src/v3/entrenar.py +
src/v3/entrenar_final.py + src/v3/ensemble.py). Lo único nuevo es el peso
de las filas de octubre (--peso_nuevos), para poder correr la línea base con
el MISMO código y el MISMO archivo: --peso_nuevos 0 las elimina del train.

Receta (Optuna, 20 pruebas, hpo_robertuito_mejor.json):
    pysentimiento/robertuito-base-cased · texto_modelo SIN pasar a minúsculas
    lr 5.7309e-5 · batch 32 · 6 épocas · wd 0.017565 · warmup 0.092922
    peso por muestra: real 1.0 · sintético 0.75 · pérdida = Σ(w·ℓ)/Σw
    pesos por clase len/(4·n_c) · early stopping paciencia 2 sobre F1-macro val
    3 semillas (42, 1337, 2026) · ensemble = promedio de las 3, sin selección

Salidas en --out:
    semilla_<s>/probs_{val,test,adv}.npy   probabilidades por semilla
    preds_test.csv  (ID,y_pred)            ensemble sobre test
    preds_adv.csv                          ensemble sobre la batería de 144
    probs_test.npy · metricas.json
"""
import argparse, json, random, shutil, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import f1_score
from transformers import (AutoTokenizer, AutoModelForSequenceClassification, Trainer,
                          TrainingArguments, DataCollatorWithPadding, EarlyStoppingCallback)

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar  # noqa: E402  (v1.2, la de la Etapa II)

CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MODELO_BASE = "pysentimiento/robertuito-base-cased"
MAX_LEN = 128
ORIGEN_NUEVOS = "real_x_oct2026"


def args_():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--val", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--adv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1337, 2026])
    ap.add_argument("--lr", type=float, default=5.730860472639071e-05)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epocas", type=int, default=6)
    ap.add_argument("--wd", type=float, default=0.017565211585462696)
    ap.add_argument("--warmup", type=float, default=0.09292202855971166)
    ap.add_argument("--peso_sintetico", type=float, default=0.75)
    ap.add_argument("--peso_nuevos", type=float, default=1.0,
                    help="peso de las filas origen=real_x_oct2026; 0 = línea base sin ellas")
    ap.add_argument("--excluir_fuera_sv", action="store_true")
    ap.add_argument("--guardar_modelos", action="store_true")
    ap.add_argument("--modelo_base", default=MODELO_BASE, help="solo para pruebas; no cambiar")
    return ap.parse_args()


def fijar_semilla(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


class DS(torch.utils.data.Dataset):
    def __init__(self, enc, labels, pesos=None):
        self.enc, self.labels, self.pesos = enc, np.asarray(labels), pesos

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        item = {k: v[i] for k, v in self.enc.items()}
        item["labels"] = int(self.labels[i])
        if self.pesos is not None:
            item["peso_muestra"] = float(self.pesos[i])
        return item


class Colador(DataCollatorWithPadding):
    def __call__(self, feats):
        pm = [f.pop("peso_muestra") for f in feats] if "peso_muestra" in feats[0] else None
        b = super().__call__(feats)
        if pm is not None:
            b["peso_muestra"] = torch.tensor(pm, dtype=torch.float)
        return b


class TrainerPesado(Trainer):
    """Igual que src/v3/entrenar.py: pesos por clase y por muestra, normalizado por Σw."""
    def __init__(self, *a, pesos_clase=None, **k):
        super().__init__(*a, **k)
        self.pesos_clase = pesos_clase

    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        labels = inputs.pop("labels")
        pm = inputs.pop("peso_muestra", None)
        out = model(**inputs)
        w = self.pesos_clase.to(out.logits.device) if self.pesos_clase is not None else None
        if pm is None:
            loss = nn.CrossEntropyLoss(weight=w)(out.logits, labels)
        else:
            l = nn.CrossEntropyLoss(weight=w, reduction="none")(out.logits, labels)
            pm = pm.to(l.device).float()
            loss = (l * pm).sum() / pm.sum().clamp(min=1e-8)
        return (loss, out) if return_outputs else loss


def f1m(y, p):
    return f1_score(y, p, average="macro", zero_division=0)


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)


def main():
    a = args_()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tr, va, te = (pd.read_csv(p) for p in (a.train, a.val, a.test))
    adv = pd.read_csv(a.adv)

    if a.excluir_fuera_sv and "fuera_de_sv" in tr.columns:
        tr = tr[~tr.fuera_de_sv.astype(str).str.lower().eq("true")]
    origen = tr["origen"].astype(str)
    pesos = np.where(origen.eq("real"), 1.0,
                     np.where(origen.eq(ORIGEN_NUEVOS), a.peso_nuevos, a.peso_sintetico))
    keep = pesos > 0
    tr, pesos = tr[keep].reset_index(drop=True), pesos[keep]
    cnt = np.bincount(tr.label.values, minlength=4)
    pesos_clase = torch.tensor(len(tr) / (4 * cnt), dtype=torch.float)
    n_nuevas = int(tr.origen.astype(str).eq(ORIGEN_NUEVOS).sum())
    print(f"train efectivo: {len(tr)} filas ({n_nuevas} de octubre) | por clase {cnt.tolist()} "
          f"| pesos clase {pesos_clase.numpy().round(4).tolist()}", flush=True)

    tok = AutoTokenizer.from_pretrained(a.modelo_base)
    enc = lambda s: tok([str(t) for t in s], truncation=True, max_length=MAX_LEN)
    d_tr = DS(enc(tr.texto_modelo), tr.label.values, pesos)
    d_va = DS(enc(va.texto_modelo), va.label.values)
    d_te = DS(enc(te.texto_modelo), te.label.values)
    # Batería: se normaliza desde el texto crudo con el normalizador vigente (como ensemble.py)
    d_adv = DS(enc([normalizar(str(t)) for t in adv.texto]), adv.label_esperado.values)

    por_semilla, P = {}, {"val": [], "test": [], "adv": []}
    for s in a.seeds:
        ds = out / f"semilla_{s}"
        if (ds / "probs_test.npy").exists():          # reanudar tras una desconexión
            for c in P:
                P[c].append(np.load(ds / f"probs_{c}.npy"))
            por_semilla[s] = json.loads((ds / "resumen.json").read_text())
            print(f"semilla {s}: ya estaba, se reutiliza", flush=True)
            continue
        t0 = time.time(); fijar_semilla(s)
        model = AutoModelForSequenceClassification.from_pretrained(
            a.modelo_base, num_labels=4, id2label=dict(enumerate(CLASES)),
            label2id={c: i for i, c in enumerate(CLASES)})
        ta = TrainingArguments(
            output_dir=str(out / f"_tmp_s{s}"), num_train_epochs=a.epocas, learning_rate=a.lr,
            per_device_train_batch_size=a.batch, per_device_eval_batch_size=32,
            warmup_steps=max(1, int(a.warmup * a.epocas * len(tr) / a.batch)), weight_decay=a.wd,
            eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
            metric_for_best_model="f1_macro", greater_is_better=True, save_total_limit=1,
            logging_steps=50, report_to=[], seed=s, disable_tqdm=True,
            remove_unused_columns=False, fp16=torch.cuda.is_available(), dataloader_pin_memory=False)
        trn = TrainerPesado(
            model=model, args=ta, train_dataset=d_tr, eval_dataset=d_va,
            data_collator=Colador(tok), pesos_clase=pesos_clase,
            compute_metrics=lambda e: {"f1_macro": f1m(e.label_ids, e.predictions.argmax(-1))},
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
        trn.train()
        ds.mkdir(parents=True, exist_ok=True)
        for c, d in [("val", d_va), ("test", d_te), ("adv", d_adv)]:
            p = softmax(trn.predict(d).predictions.astype(np.float64))
            np.save(ds / f"probs_{c}.npy", p); P[c].append(p)
        por_semilla[s] = {"f1_val": f1m(va.label.values, P["val"][-1].argmax(1)),
                          "f1_test": f1m(te.label.values, P["test"][-1].argmax(1)),
                          "minutos": round((time.time() - t0) / 60, 2)}
        (ds / "resumen.json").write_text(json.dumps(por_semilla[s]))
        if a.guardar_modelos:
            trn.save_model(str(ds / "modelo")); tok.save_pretrained(str(ds / "modelo"))
        shutil.rmtree(out / f"_tmp_s{s}", ignore_errors=True)
        print(f"semilla {s}: val {por_semilla[s]['f1_val']:.4f} · test {por_semilla[s]['f1_test']:.4f} "
              f"· {por_semilla[s]['minutos']} min", flush=True)
        del model, trn; torch.cuda.empty_cache()

    # Ensemble: promedio de las tres semillas, regla fijada de antemano (sin elegir)
    y = te.label.values
    pt = np.mean(P["test"], 0); pred = pt.argmax(1)
    pa = np.mean(P["adv"], 0).argmax(1)
    pd.DataFrame({"ID": te.ID, "y_pred": pred}).to_csv(out / "preds_test.csv", index=False)
    pd.DataFrame({"ID": adv.ID, "grupo": adv.grupo_de_prueba, "y_true": adv.label_esperado,
                  "y_pred": pa}).to_csv(out / "preds_adv.csv", index=False)
    np.save(out / "probs_test.npy", pt)
    res = {"config": vars(a), "modelo_base": a.modelo_base, "train_efectivo": int(len(tr)),
           "filas_octubre": n_nuevas, "por_semilla": por_semilla,
           "ensemble_f1_val": f1m(va.label.values, np.mean(P["val"], 0).argmax(1)),
           "ensemble_f1_test": f1m(y, pred), "ensemble_aciertos": int((pred == y).sum()),
           "bateria_144": int((pa == adv.label_esperado.values).sum())}
    json.dump(res, open(out / "metricas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=float)
    print(json.dumps({k: res[k] for k in ["ensemble_f1_val", "ensemble_f1_test", "ensemble_aciertos", "bateria_144"]},
                     indent=2), flush=True)


if __name__ == "__main__":
    main()
