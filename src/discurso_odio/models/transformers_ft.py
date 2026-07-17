"""Fine-tuning ligero de modelos Transformer (mBERT y XLM-R)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from discurso_odio.data.taxonomy import CANONICAL_LABELS, LABEL_TO_ID
from discurso_odio.models.evaluate import compute_metrics as sklearn_metrics
from discurso_odio.utils.paths import get_models_dir, get_project_root

MODEL_CONFIGS = {
    "mbert": {
        "model_name": "bert-base-multilingual-cased",
        "output_dir": "mbert-ft-demo",
        "issue": "TFM-27",
    },
    "xlmr": {
        "model_name": "xlm-roberta-base",
        "output_dir": "xlmr-ft-demo",
        "issue": "TFM-28",
    },
}


def _compute_metrics(eval_pred):
    """Métricas para el Trainer de Hugging Face."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    id_to_label = {v: k for k, v in LABEL_TO_ID.items()}
    y_true = [id_to_label[int(l)] for l in labels]
    y_pred = [id_to_label[int(p)] for p in predictions]
    return {k: v for k, v in sklearn_metrics(y_true, y_pred).items()}


def _prepare_hf_dataset(
    texts: pd.Series,
    labels: pd.Series,
    tokenizer,
    max_length: int = 128,
    sample_size: int = 400,
) -> tuple[Dataset, Dataset]:
    """Prepara subset para fine-tuning demostrativo."""
    df = pd.DataFrame({"text": texts, "label": labels.map(LABEL_TO_ID)})
    if len(df) > sample_size:
        df, _ = train_test_split(
            df,
            train_size=sample_size,
            random_state=42,
            stratify=df["label"],
        )

    train_df, eval_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"]
    )

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

    train_ds = Dataset.from_pandas(train_df.reset_index(drop=True))
    eval_ds = Dataset.from_pandas(eval_df.reset_index(drop=True))
    train_ds = train_ds.map(tokenize, batched=True)
    eval_ds = eval_ds.map(tokenize, batched=True)
    return train_ds, eval_ds


def fine_tune_transformer(
    texts: pd.Series,
    labels: pd.Series,
    model_key: str = "mbert",
    epochs: int = 1,
    sample_size: int = 200,
    max_length: int = 64,
) -> dict:
    """Fine-tuning ligero de mBERT o XLM-R para demostración."""
    if model_key not in MODEL_CONFIGS:
        raise ValueError(f"Modelo desconocido: {model_key}")

    config = MODEL_CONFIGS[model_key]
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    model = AutoModelForSequenceClassification.from_pretrained(
        config["model_name"],
        num_labels=len(CANONICAL_LABELS),
        id2label={i: l for i, l in enumerate(CANONICAL_LABELS)},
        label2id=LABEL_TO_ID,
    )

    train_ds, eval_ds = _prepare_hf_dataset(
        texts, labels, tokenizer, max_length=max_length, sample_size=sample_size
    )
    output_dir = get_models_dir() / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=20,
        learning_rate=2e-5,
        weight_decay=0.01,
        report_to="none",
        use_cpu=not torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        compute_metrics=_compute_metrics,
    )

    train_result = trainer.train()
    eval_metrics = trainer.evaluate()

    # Guardar modelo y métricas
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    metrics_path = get_project_root() / "reports" / f"finetune_{model_key}_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "model_key": model_key,
                "model_name": config["model_name"],
                "issue": config["issue"],
                "train_loss": float(train_result.training_loss),
                "eval_metrics": {k: float(v) for k, v in eval_metrics.items() if isinstance(v, (int, float))},
                "sample_size": sample_size,
                "epochs": epochs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    return {
        "output_dir": str(output_dir),
        "metrics_path": str(metrics_path),
        "eval_metrics": eval_metrics,
    }


def run_all_finetuning(texts: pd.Series, labels: pd.Series) -> dict:
    """Ejecuta fine-tuning ligero de mBERT y XLM-R."""
    results = {}
    for key in MODEL_CONFIGS:
        results[key] = fine_tune_transformer(texts, labels, model_key=key)
    return results
