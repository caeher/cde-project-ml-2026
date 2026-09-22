# -*- coding: utf-8 -*-
"""CLI del motor V3: build-data, tune, train, evaluate."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

from modeling_v3.constants import DEFAULT_MODEL, DEFAULT_SEED
from modeling_v3.data import leer_csv, reconstruir, validar_contrato
from modeling_v3.evaluation import evaluar
from modeling_v3.paths import default_data_dir, default_models_dir
from modeling_v3.training import entrenar


def _sample_train(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if len(df) <= n:
        return df
    parts = []
    for _, g in df.groupby("label"):
        k = max(1, int(round(n * len(g) / len(df))))
        parts.append(g.sample(n=min(k, len(g)), random_state=seed))
    out = pd.concat(parts)
    return out.sample(n=min(n, len(out)), random_state=seed).reset_index(drop=True)


def cmd_build_data(args: argparse.Namespace) -> int:
    data_dir = Path(args.data_dir)
    if args.reconstruir:
        reconstruir(data_dir)
        return 0
    res = validar_contrato(data_dir)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["ok"] else 1


def cmd_train(args: argparse.Namespace) -> int:
    train_path = Path(args.train)
    salida = Path(args.salida)
    train_csv = train_path
    tmp: Path | None = None
    if args.rapido:
        df = _sample_train(leer_csv(train_path), n=args.rapido_filas, seed=args.semilla)
        tmp = Path(tempfile.mkstemp(suffix=".csv")[1])
        df.to_csv(tmp, index=False)
        train_csv = tmp
    try:
        res = entrenar(
            args.modelo,
            args.alias,
            train_csv,
            salida,
            epochs=1 if args.rapido else args.epochs,
            lr=args.lr,
            bs=args.batch_size,
            semilla=args.semilla,
            guardar=not args.rapido,
            peso_sintetico=args.peso_sintetico,
            solo_reales_al_final=args.fases_reales,
            val_csv=Path(args.val) if args.val else None,
        )
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    out = Path(args.salida) / "entrenamiento.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))
    return 0


def cmd_tune(args: argparse.Namespace) -> int:
    from modeling_v3.hpo import ejecutar_hpo

    mejor = ejecutar_hpo(
        args.modelo,
        Path(args.salida),
        n_pruebas=args.trials,
        train_csv=Path(args.train) if args.train else None,
        rapido=args.rapido,
    )
    print(json.dumps(mejor, indent=2, ensure_ascii=False))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    salida = Path(args.salida)
    res = evaluar(
        Path(args.modelo),
        args.alias,
        salida,
        data_dir=Path(args.data_dir),
        sonda_csv=Path(args.sonda) if args.sonda else None,
        referencia_logits_dir=Path(args.referencia_logits) if args.referencia_logits else None,
        bootstrap_samples=100 if args.rapido else 4000,
    )
    print(
        f"F1-macro test: {res['test']['f1_macro']:.4f} "
        f"(ref 0.8499 ±0.01 tolerancia)"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m modeling_v3.cli")
    sub = p.add_subparsers(dest="command", required=True)

    bd = sub.add_parser("build-data", help="Validar splits congelados en data/processed/v3")
    bd.add_argument("--data-dir", default=str(default_data_dir()))
    bd.add_argument(
        "--reconstruir",
        action="store_true",
        help="Reconstruir train (requiere lexicon_salvadoreno.csv)",
    )
    bd.set_defaults(func=cmd_build_data)

    tr = sub.add_parser("train", help="Entrenar un checkpoint V3")
    tr.add_argument("--modelo", default=DEFAULT_MODEL)
    tr.add_argument("--alias", default="v3")
    tr.add_argument("--train", default=str(default_data_dir() / "train.csv"))
    tr.add_argument("--val", default=None)
    tr.add_argument("--salida", default=str(default_models_dir() / "v3"))
    tr.add_argument("--epochs", type=int, default=4)
    tr.add_argument("--lr", type=float, default=2e-5)
    tr.add_argument("--batch-size", type=int, default=16)
    tr.add_argument("--semilla", type=int, default=DEFAULT_SEED)
    tr.add_argument("--peso-sintetico", type=float, default=None)
    tr.add_argument("--fases-reales", type=int, default=0)
    tr.add_argument(
        "--rapido",
        action="store_true",
        help="Subconjunto pequeño, 1 época, sin guardar pesos (requiere GPU)",
    )
    tr.add_argument("--rapido-filas", type=int, default=128)
    tr.set_defaults(func=cmd_train)

    tu = sub.add_parser("tune", help="Búsqueda de hiperparámetros (Optuna)")
    tu.add_argument("--modelo", default=DEFAULT_MODEL)
    tu.add_argument("--train", default=None)
    tu.add_argument("--salida", default=str(default_models_dir() / "hpo"))
    tu.add_argument("--trials", type=int, default=20)
    tu.add_argument(
        "--rapido",
        action="store_true",
        help="3 trials y 1 época por trial (requiere GPU)",
    )
    tu.set_defaults(func=cmd_tune)

    ev = sub.add_parser("evaluate", help="Evaluar checkpoint sobre test/val")
    ev.add_argument("modelo", help="Ruta al directorio del modelo")
    ev.add_argument("alias", help="Nombre del experimento")
    ev.add_argument("--data-dir", default=str(default_data_dir()))
    ev.add_argument("--salida", default=str(default_models_dir() / "eval"))
    ev.add_argument("--sonda", default=None, help="CSV sonda opcional (auditoría 2v)")
    ev.add_argument("--referencia-logits", default=None, help="Directorio logits McNemar opcional")
    ev.add_argument("--rapido", action="store_true", help="Bootstrap reducido")
    ev.set_defaults(func=cmd_evaluate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
