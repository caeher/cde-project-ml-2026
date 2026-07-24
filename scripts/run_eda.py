#!/usr/bin/env python
"""Ejecuta el análisis exploratorio de datos (EDA)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json

from discurso_odio.config import load_config
from discurso_odio.data.agreement import save_kappa_report
from discurso_odio.data.loader import load_dataset, prepare_dataset
from discurso_odio.eda.analysis import run_full_eda
from discurso_odio.eda.stats import get_dataset_summary
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.utils.paths import get_data_dir, get_project_root


def main() -> None:
    config = load_config()
    print(f"Proyecto: {config['project']['name']}")
    df = load_dataset("unificado")
    prepared = prepare_dataset(df)
    processed = preprocess_dataframe(prepared)
    processed.to_csv(get_data_dir("processed") / "dataset_procesado.csv", index=False)
    figures = run_full_eda(prepared)
    kappa_path = save_kappa_report(prepared)
    stats_path = get_project_root() / "reports" / "dataset_summary.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(get_dataset_summary(), f, indent=2, ensure_ascii=False)
    print(f"Filas procesadas: {len(processed)}")
    print(f"Figuras generadas: {len(figures)}")
    for fig in figures:
        print(f"  - {fig}")
    print(f"Reporte Kappa: {kappa_path}")
    print(f"Resumen dataset: {stats_path}")


if __name__ == "__main__":
    main()
