#!/usr/bin/env python
"""Ejecuta validación cruzada entre anotadores y actualiza los CSV."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discurso_odio.data.agreement import save_kappa_report
from discurso_odio.data.loader import DATASET_FILES, load_raw_dataset
from discurso_odio.data.validation import apply_validation_protocol
from discurso_odio.utils.paths import get_data_dir


def main() -> None:
    unificado = load_raw_dataset(DATASET_FILES["unificado"])
    validated = apply_validation_protocol(unificado)

    raw_dir = get_data_dir("raw")
    for filename in DATASET_FILES.values():
        path = raw_dir / filename
        if not path.exists():
            continue
        df = load_raw_dataset(filename)
        if "ID" not in df.columns or "ID" not in validated.columns:
            validated.to_csv(raw_dir / DATASET_FILES["unificado"], index=False)
            break
        merge_cols = [
            "Validado",
            "Validador",
            "Fecha_Validacion",
            "Acuerdo_Validador",
            "Cohen_Kappa",
            "Clase_Validador",
        ]
        cols = [c for c in merge_cols if c in validated.columns]
        updates = validated[["ID", *cols]].drop_duplicates(subset=["ID"])
        merged = df.drop(columns=[c for c in cols if c in df.columns], errors="ignore")
        merged = merged.merge(updates, on="ID", how="left")
        merged.to_csv(path, index=False)
        print(f"Actualizado: {path} ({len(merged)} filas)")

    kappa_path = save_kappa_report(validated)
    print(f"Reporte Kappa: {kappa_path}")


if __name__ == "__main__":
    main()
