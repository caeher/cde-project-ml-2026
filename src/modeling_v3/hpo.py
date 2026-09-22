# -*- coding: utf-8 -*-
"""Búsqueda de hiperparámetros con Optuna (F1-macro en validación)."""

from __future__ import annotations

import json
from pathlib import Path

import optuna

from modeling_v3.paths import default_data_dir, default_models_dir
from modeling_v3.training import entrenar

optuna.logging.set_verbosity(optuna.logging.WARNING)


def ejecutar_hpo(
    modelo_hf: str,
    salida: Path,
    *,
    n_pruebas: int = 20,
    train_csv: Path | None = None,
    rapido: bool = False,
) -> dict:
    train = train_csv if train_csv is not None else default_data_dir() / "train.csv"
    salida.mkdir(parents=True, exist_ok=True)
    registro: list[dict] = []
    scratch = default_models_dir() / "_hpo"
    trials = 3 if rapido else n_pruebas

    def objetivo(t: optuna.Trial) -> float:
        cfg = {
            "lr": round(t.suggest_float("lr", 8e-6, 6e-5, log=True), 8),
            "bs": t.suggest_categorical("bs", [8, 16, 32]),
            "epochs": t.suggest_int("epochs", 3, 6),
            "weight_decay": round(t.suggest_float("weight_decay", 0.0, 0.15), 4),
            "warmup": round(t.suggest_float("warmup", 0.0, 0.2), 4),
            "peso_sintetico": t.suggest_categorical("peso_sintetico", [0.25, 0.5, 0.75, 1.0]),
            "fases_reales": t.suggest_int("fases_reales", 0, 3),
            "pesos_clase": t.suggest_categorical("pesos_clase", [True, False]),
        }
        try:
            r = entrenar(
                modelo_hf,
                f"hpo_{t.number}",
                train,
                scratch,
                epochs=1 if rapido else cfg["epochs"],
                lr=cfg["lr"],
                bs=cfg["bs"],
                weight_decay=cfg["weight_decay"],
                warmup=cfg["warmup"],
                peso_sintetico=cfg["peso_sintetico"],
                solo_reales_al_final=cfg["fases_reales"],
                pesos=cfg["pesos_clase"],
                guardar=False,
            )
        except Exception:
            raise optuna.TrialPruned() from None
        registro.append(
            {**cfg, "trial": t.number, "val_f1_macro": r["val_f1_macro"], "minutos": r["minutos"]}
        )
        (salida / "hpo_historial.json").write_text(
            json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return r["val_f1_macro"]

    est = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=42)
    )
    est.optimize(objetivo, n_trials=trials, catch=())

    mejor = {
        "modelo": modelo_hf,
        "train": str(train),
        "n_pruebas": trials,
        "mejores_parametros": est.best_params,
        "mejor_val_f1": est.best_value,
        "historial": registro,
    }
    (salida / "hpo_mejor.json").write_text(
        json.dumps(mejor, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return mejor
