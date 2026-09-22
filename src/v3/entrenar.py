# -*- coding: utf-8 -*-
"""
Banco de entrenamiento V3. Una sola función para todos los candidatos, con
hiperparámetros idénticos, para que la comparación de arquitecturas sea limpia.

Contrato invariable: 4 clases, max_length=128, columna texto_modelo, semilla 42.
val y test nunca se modifican.
"""
import argparse, json, os, random, time
import sys
from pathlib import Path

import numpy as np, pandas as pd, torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from torch import nn
from sklearn.metrics import f1_score, accuracy_score
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, DataCollatorWithPadding,
                          EarlyStoppingCallback)
from datasets import Dataset

RAIZ = Path(__file__).resolve().parents[2]
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
MAX_LEN = 128


def fijar_semilla(s=42):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def leer(p):
    d = pd.read_csv(p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d


def metricas(pred):
    y = pred.label_ids; p = pred.predictions.argmax(-1)
    return {"f1_macro": f1_score(y, p, average="macro", zero_division=0),
            "accuracy": accuracy_score(y, p)}


class TrainerPesado(Trainer):
    """
    CrossEntropy con dos ponderaciones independientes:

      · por CLASE, que es lo que define el plan del proyecto;
      · por MUESTRA, para bajar la masa efectiva de los sintéticos.

    La segunda existe porque la ablación mostró que añadir sintéticos de
    plantilla cuesta F1 sobre la distribución natural: son más regulares que el
    lenguaje real y, con el mismo peso que un ejemplo recolectado, desplazan la
    frontera de decisión hacia un español que nadie escribe. Bajarles el peso
    conserva la señal de robustez sin dejar que dominen el gradiente.
    """
    def __init__(self, pesos=None, **kw):
        super().__init__(**kw)
        self.pesos = pesos

    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        labels = inputs.pop("labels")
        peso_muestra = inputs.pop("peso_muestra", None)
        out = model(**inputs)
        w = self.pesos.to(out.logits.device) if self.pesos is not None else None
        if peso_muestra is None:
            loss = nn.CrossEntropyLoss(weight=w)(out.logits, labels)
        else:
            por_ejemplo = nn.CrossEntropyLoss(weight=w, reduction="none")(out.logits, labels)
            pm = peso_muestra.to(por_ejemplo.device).float()
            loss = (por_ejemplo * pm).sum() / pm.sum().clamp(min=1e-8)
        return (loss, out) if return_outputs else loss


def preparar(tok, df, peso_sintetico=None):
    cols = ["texto_modelo", "label"]
    d = df[cols].rename(columns={"label": "labels"}).copy()
    if peso_sintetico is not None:
        es_sint = ~df["origen"].astype(str).eq("real")
        d["peso_muestra"] = [peso_sintetico if s else 1.0 for s in es_sint]
    ds = Dataset.from_pandas(d, preserve_index=False)
    return ds.map(lambda e: tok(e["texto_modelo"], truncation=True, max_length=MAX_LEN),
                  batched=True, remove_columns=["texto_modelo"])


def entrenar(modelo_hf, alias, train_csv, salida, *, epochs=4, lr=2e-5, bs=16,
             acum=1, pesos=True, tokens_nuevos=None, fp16=True, warmup=0.1,
             weight_decay=0.01, semilla=42, guardar=True, peso_sintetico=None,
             solo_reales_al_final=0, val_csv=None):
    fijar_semilla(semilla)
    t0 = time.time()
    tr = leer(train_csv)
    va = leer(val_csv if val_csv else RAIZ / "data/dataset_v3/val.csv")

    tok = AutoTokenizer.from_pretrained(modelo_hf)
    mod = AutoModelForSequenceClassification.from_pretrained(
        modelo_hf, num_labels=4,
        id2label={i: c for i, c in enumerate(CLASES)},
        label2id={c: i for i, c in enumerate(CLASES)})

    n_add = 0
    if tokens_nuevos:
        n_add = tok.add_tokens(list(tokens_nuevos))
        if n_add:
            mod.resize_token_embeddings(len(tok))

    w = None
    if pesos:
        cnt = np.bincount(tr["label"].values, minlength=4)
        w = torch.tensor(len(tr) / (4 * cnt), dtype=torch.float)

    args = TrainingArguments(
        output_dir=str(salida / "_run"),
        num_train_epochs=epochs, learning_rate=lr,
        per_device_train_batch_size=bs, per_device_eval_batch_size=32,
        gradient_accumulation_steps=acum,
        warmup_steps=max(1, int(warmup * epochs * len(tr) / (bs * acum))), weight_decay=weight_decay,
        eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="f1_macro",
        greater_is_better=True, save_total_limit=1,
        logging_steps=50, report_to=[], seed=semilla, disable_tqdm=True,
        remove_unused_columns=False,   # si no, se pierde `peso_muestra`
        fp16=fp16 and torch.cuda.is_available(),
        gradient_checkpointing="large" in modelo_hf.lower(),
        dataloader_pin_memory=False)

    trainer = TrainerPesado(
        pesos=w, model=mod, args=args,
        train_dataset=preparar(tok, tr, peso_sintetico), eval_dataset=preparar(tok, va),
        data_collator=DataCollatorWithPadding(tok), compute_metrics=metricas,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])

    trainer.train()

    # Segunda fase opcional: reajustar solo sobre los ejemplos reales.
    # El modelo llega con la robustez que aportaron los sintéticos y termina de
    # asentarse en la distribución que de verdad se va a evaluar.
    if solo_reales_al_final:
        reales = tr[tr["origen"].astype(str) == "real"]
        args2 = TrainingArguments(
            output_dir=str(salida / "_run2"),
            num_train_epochs=solo_reales_al_final, learning_rate=lr / 2,
            per_device_train_batch_size=bs, per_device_eval_batch_size=32,
            gradient_accumulation_steps=acum, warmup_steps=0,
            weight_decay=weight_decay, eval_strategy="epoch", save_strategy="epoch",
            load_best_model_at_end=True, metric_for_best_model="f1_macro",
            greater_is_better=True, save_total_limit=1, logging_steps=50,
            report_to=[], seed=semilla, disable_tqdm=True,
            remove_unused_columns=False,
            fp16=fp16 and torch.cuda.is_available(), dataloader_pin_memory=False)
        trainer2 = TrainerPesado(
            pesos=w, model=trainer.model, args=args2,
            train_dataset=preparar(tok, reales), eval_dataset=preparar(tok, va),
            data_collator=DataCollatorWithPadding(tok), compute_metrics=metricas)
        trainer2.train()
        trainer = trainer2

    ev = trainer.evaluate()
    dur = time.time() - t0

    if guardar:
        salida.mkdir(parents=True, exist_ok=True)
        trainer.save_model(str(salida)); tok.save_pretrained(str(salida))
        (salida / "inference_contract.json").write_text(json.dumps(
            {"max_length": MAX_LEN, "text_column": "texto_modelo",
             "normalizer": "normalize_for_model", "normalizer_version": "1.1"}, indent=2))

    res = dict(alias=alias, modelo_hf=modelo_hf, train_csv=str(train_csv),
               n_train=len(tr), epochs=epochs, lr=lr, bs=bs * acum,
               tokens_anadidos=n_add, semilla=semilla,
               peso_sintetico=peso_sintetico, epocas_solo_reales=solo_reales_al_final,
               val_f1_macro=float(ev["eval_f1_macro"]), val_accuracy=float(ev["eval_accuracy"]),
               minutos=round(dur / 60, 2), params=sum(p.numel() for p in mod.parameters()))
    import shutil
    shutil.rmtree(salida / "_run", ignore_errors=True)
    shutil.rmtree(salida / "_run2", ignore_errors=True)
    del mod, trainer; torch.cuda.empty_cache()
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("modelo_hf"); ap.add_argument("alias")
    ap.add_argument("--train", default=str(RAIZ / "data/dataset_b2/train.csv"))
    ap.add_argument("--salida", default=None)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--acum", type=int, default=1)
    ap.add_argument("--no-guardar", action="store_true")
    ap.add_argument("--vocab", action="store_true", help="añadir los tokens de dominio")
    ap.add_argument("--peso-sintetico", type=float, default=None)
    ap.add_argument("--fases-reales", type=int, default=0)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--warmup", type=float, default=0.1)
    ap.add_argument("--sin-pesos-clase", action="store_true")
    ap.add_argument("--json-salida", default=None)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--val", default=None, help="CSV de validación alternativo (para CV)")
    a = ap.parse_args()
    toks = None
    if a.vocab:
        from src.v3.tokens_dominio import todos
        toks = todos()
    sal = Path(a.salida) if a.salida else RAIZ / "models/v3" / a.alias
    r = entrenar(a.modelo_hf, a.alias, a.train, sal, epochs=a.epochs, lr=a.lr,
                 bs=a.bs, acum=a.acum, guardar=not a.no_guardar, tokens_nuevos=toks,
                 peso_sintetico=a.peso_sintetico, solo_reales_al_final=a.fases_reales,
                 weight_decay=a.weight_decay, warmup=a.warmup, pesos=not a.sin_pesos_clase,
                 semilla=a.semilla, val_csv=a.val)
    if a.json_salida:
        Path(a.json_salida).write_text(json.dumps(r, ensure_ascii=False))
    print("\nRESULTADO " + json.dumps(r, ensure_ascii=False))
