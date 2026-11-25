"""Fija la columna `anotador` en los CSV de hilos al roster Willian / Cristian / Julio."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

ASIGNACION: dict[Path, str] = {
    RAIZ / "data/annotation/threads/hilos_etiquetados.csv": "Willian",
    RAIZ / "data/annotation/threads/hilos_etiquetados_2.csv": "Cristian",
    RAIZ / "data/annotation/threads/test_externo_cecot.csv": "Julio",
    RAIZ / "data/history/v1.4.0-a/hilos_reservados.csv": "Willian",
}


def main() -> None:
    for path, nombre in ASIGNACION.items():
        if not path.is_file():
            print(f"omitido (no existe): {path}")
            continue
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
        if "anotador" not in df.columns:
            print(f"omitido (sin columna anotador): {path}")
            continue
        antes = df["anotador"].nunique()
        df["anotador"] = nombre
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"{path.relative_to(RAIZ)}: anotador={nombre} (antes {antes} valores distintos, {len(df)} filas)")


if __name__ == "__main__":
    main()
