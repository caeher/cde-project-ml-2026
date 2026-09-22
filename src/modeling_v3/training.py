# -*- coding: utf-8 -*-
"""Entrenamiento fine-tuning V3 (contrato: 4 clases, max_length=128, texto_modelo)."""

from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

from modeling_v3.constants import CLASES, DEFAULT_SEED, MAX_LEN, TEXT_COLUMN
from modeling_v3.data import leer_csv
from modeling_v3.device import require_cuda
from modeling_v3.paths import default_data_dir


def fijar_semilla(s: int = DEFAULT_SEED) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


def metricas(pred):
    y = pred.label_ids
    p = pred.predictions.argmax(-1)
    return {
        "f1_macro": f1_score(y, p, average="macro", zero_division=0),
        "accuracy": accuracy_score(y, p),
    }


class TrainerPesado(Trainer):
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
    cols = [TEXT_COLUMN, "label"]
    d = df[cols].rename(columns={"label": "labels"}).copy()
    if peso_sintetico is not None and "origen" in df.columns:
        es_sint = ~df["origen"].astype(str).eq("real")
        d["peso_muestra"] = [peso_sintetico if s else 1.0 for s in es_sint]
    ds = Dataset.from_pandas(d, preserve_index=False)
    return ds.map(
        lambda e: tok(e[TEXT_COLUMN], truncation=True, max_length=MAX_LEN),
        batched=True,
        remove_columns=[TEXT_COLUMN],
    )


def entrenar(
    modelo_hf: str,
    alias: str,
    train_csv: Path,
    salida: Path,
    *,
    epochs: int = 4,
    lr: float = 2e-5,
    bs: int = 16,
    acum: int = 1,
    pesos: bool = True,
    fp16: bool = True,
    warmup: float = 0.1,
    weight_decay: float = 0.01,
    semilla: int = DEFAULT_SEED,
    guardar: bool = True,
    peso_sintetico: float | None = None,
    solo_reales_al_final: int = 0,
    val_csv: Path | None = None,
) -> dict:
    dev = require_cuda()
    fijar_semilla(semilla)
    t0 = time.time()
    tr = leer_csv(train_csv)
    va_path = val_csv if val_csv is not None else default_data_dir() / "val.csv"
    va = leer_csv(va_path)

    tok = AutoTokenizer.from_pretrained(modelo_hf)
    mod = AutoModelForSequenceClassification.from_pretrained(
        modelo_hf,
        num_labels=4,
        id2label={i: c for i, c in enumerate(CLASES)},
        label2id={c: i for i, c in enumerate(CLASES)},
    )

    w = None
    if pesos:
        cnt = np.bincount(tr["label"].values, minlength=4)
        w = torch.tensor(len(tr) / (4 * cnt), dtype=torch.float)

    args = TrainingArguments(
        output_dir=str(salida / "_run"),
        num_train_epochs=epochs,
        learning_rate=lr,
        per_device_train_batch_size=bs,
        per_device_eval_batch_size=32,
        gradient_accumulation_steps=acum,
        warmup_steps=max(1, int(warmup * epochs * len(tr) / (bs * acum))),
        weight_decay=weight_decay,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=1,
        logging_steps=50,
        report_to=[],
        seed=semilla,
        disable_tqdm=True,
        remove_unused_columns=False,
        fp16=fp16,
        gradient_checkpointing="large" in modelo_hf.lower(),
        dataloader_pin_memory=True,
    )
    mod.to(dev)

    trainer = TrainerPesado(
        pesos=w,
        model=mod,
        args=args,
        train_dataset=preparar(tok, tr, peso_sintetico),
        eval_dataset=preparar(tok, va),
        data_collator=DataCollatorWithPadding(tok),
        compute_metrics=metricas,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )
    trainer.train()

    if solo_reales_al_final and "origen" in tr.columns:
        reales = tr[tr["origen"].astype(str) == "real"]
        args2 = TrainingArguments(
            output_dir=str(salida / "_run2"),
            num_train_epochs=solo_reales_al_final,
            learning_rate=lr / 2,
            per_device_train_batch_size=bs,
            per_device_eval_batch_size=32,
            gradient_accumulation_steps=acum,
            warmup_steps=0,
            weight_decay=weight_decay,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1_macro",
            greater_is_better=True,
            save_total_limit=1,
            logging_steps=50,
            report_to=[],
            seed=semilla,
            disable_tqdm=True,
            remove_unused_columns=False,
            fp16=fp16,
            dataloader_pin_memory=True,
        )
        trainer2 = TrainerPesado(
            pesos=w,
            model=trainer.model,
            args=args2,
            train_dataset=preparar(tok, reales),
            eval_dataset=preparar(tok, va),
            data_collator=DataCollatorWithPadding(tok),
            compute_metrics=metricas,
        )
        trainer2.train()
        trainer = trainer2

    ev = trainer.evaluate()
    dur = time.time() - t0

    if guardar:
        salida.mkdir(parents=True, exist_ok=True)
        trainer.save_model(str(salida))
        tok.save_pretrained(str(salida))
        (salida / "inference_contract.json").write_text(
            json.dumps(
                {
                    "max_length": MAX_LEN,
                    "text_column": TEXT_COLUMN,
                    "normalizer": "modeling_v3.normalization.normalizar",
                    "normalizer_version": "1.2",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    res = {
        "alias": alias,
        "modelo_hf": modelo_hf,
        "train_csv": str(train_csv),
        "n_train": len(tr),
        "epochs": epochs,
        "lr": lr,
        "bs": bs * acum,
        "semilla": semilla,
        "peso_sintetico": peso_sintetico,
        "epocas_solo_reales": solo_reales_al_final,
        "val_f1_macro": float(ev["eval_f1_macro"]),
        "val_accuracy": float(ev["eval_accuracy"]),
        "minutos": round(dur / 60, 2),
        "params": sum(p.numel() for p in mod.parameters()),
    }

    shutil.rmtree(salida / "_run", ignore_errors=True)
    shutil.rmtree(salida / "_run2", ignore_errors=True)
    del mod, trainer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return res
