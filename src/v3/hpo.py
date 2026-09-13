# -*- coding: utf-8 -*-
"""
Etapa 3: búsqueda de hiperparámetros con Optuna.

Es el criterio de la rúbrica que estaba en cero: el proyecto documentaba los
hiperparámetros usados, nunca una búsqueda. Se optimiza F1-macro sobre
validación; el test no participa ni se mira.

Cada prueba corre en su propio proceso, por la misma razón que la ablación:
encadenar entrenamientos en un solo intérprete termina en un fallo CUDA.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

import optuna

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "reports/v3_arquitectura"
optuna.logging.set_verbosity(optuna.logging.WARNING)


def entrenar_aislado(modelo_hf: str, alias: str, train: Path, cfg: dict) -> dict | None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    cmd = [sys.executable, str(RAIZ / "src/v3/entrenar.py"), modelo_hf, alias,
           "--train", str(train), "--salida", str(RAIZ / "models/v3/_hpo"),
           "--json-salida", str(tmp), "--no-guardar",
           "--epochs", str(cfg["epochs"]), "--lr", str(cfg["lr"]),
           "--bs", str(cfg["bs"]), "--weight-decay", str(cfg["weight_decay"]),
           "--warmup", str(cfg["warmup"]),
           "--peso-sintetico", str(cfg["peso_sintetico"]),
           "--fases-reales", str(cfg["fases_reales"])]
    if not cfg["pesos_clase"]:
        cmd.append("--sin-pesos-clase")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if tmp.exists() and tmp.stat().st_size:
        d = json.loads(tmp.read_text()); tmp.unlink(); return d
    tmp.unlink(missing_ok=True)
    cola = [l for l in r.stderr.strip().split("\n") if l.strip()][-1:] or ["sin detalle"]
    print(f"    falló: {cola[0][:120]}", flush=True)
    return None


def main(modelo_hf: str, base: str, n_pruebas: int = 20,
         train: Path = RAIZ / "data/dataset_v3/train.csv"):
    registro: list[dict] = []
    ruta = SALIDA / f"hpo_{base}.json"

    def objetivo(t: optuna.Trial) -> float:
        cfg = dict(
            lr=round(t.suggest_float("lr", 8e-6, 6e-5, log=True), 8),
            bs=t.suggest_categorical("bs", [8, 16, 32]),
            epochs=t.suggest_int("epochs", 3, 6),
            weight_decay=round(t.suggest_float("weight_decay", 0.0, 0.15), 4),
            warmup=round(t.suggest_float("warmup", 0.0, 0.2), 4),
            peso_sintetico=t.suggest_categorical("peso_sintetico", [0.25, 0.5, 0.75, 1.0]),
            fases_reales=t.suggest_int("fases_reales", 0, 3),
            pesos_clase=t.suggest_categorical("pesos_clase", [True, False]),
        )
        r = entrenar_aislado(modelo_hf, f"hpo_{t.number}", train, cfg)
        if r is None:
            raise optuna.TrialPruned()
        registro.append({**cfg, "trial": t.number,
                         "val_f1_macro": r["val_f1_macro"], "minutos": r["minutos"]})
        ruta.write_text(json.dumps(registro, indent=2, ensure_ascii=False))
        print(f"  trial {t.number:2d}  F1={r['val_f1_macro']:.4f}  "
              f"lr={cfg['lr']:.2e} bs={cfg['bs']} ep={cfg['epochs']} "
              f"p_sint={cfg['peso_sintetico']} fases={cfg['fases_reales']} "
              f"pesos={cfg['pesos_clase']}", flush=True)
        return r["val_f1_macro"]

    est = optuna.create_study(direction="maximize",
                              sampler=optuna.samplers.TPESampler(seed=42))
    est.optimize(objetivo, n_trials=n_pruebas, catch=())

    mejor = {"modelo": modelo_hf, "train": str(train), "n_pruebas": n_pruebas,
             "mejores_parametros": est.best_params, "mejor_val_f1": est.best_value,
             "historial": registro}
    (SALIDA / f"hpo_{base}_mejor.json").write_text(
        json.dumps(mejor, indent=2, ensure_ascii=False))
    print(f"\n{'='*66}\nMEJOR  F1={est.best_value:.4f}\n{est.best_params}")
    return mejor


if __name__ == "__main__":
    tr = RAIZ / "data/dataset_v3/train.csv"
    if len(sys.argv) > 4:
        tr = Path(sys.argv[4])
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20, tr)
