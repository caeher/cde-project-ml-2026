# -*- coding: utf-8 -*-
"""Extrae los textos en que dos anotadores ciegos no coinciden, SIN sus etiquetas, para que un tercero desempate a ciegas.

Uso: python src/data/threads/desacuerdos.py --lote L.csv --a salida_a.csv --b salida_b.csv --salida desacuerdo.csv
Comprueba que ambas salidas cubran exactamente los ID del lote (código 2 si no). Escribe ID,texto de los desacuerdos.
"""
import argparse, sys
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    for k in ["lote", "a", "b", "salida"]: ap.add_argument(f"--{k}", required=True)
    x = ap.parse_args()
    lote = pd.read_csv(x.lote, encoding="utf-8-sig", dtype={"ID": str})
    ids = set(lote.ID)
    sal = {}
    for k in ["a", "b"]:
        s = pd.read_csv(getattr(x, k), encoding="utf-8-sig", dtype={"ID": str})
        if set(s.ID) != ids or s.ID.duplicated().any() or not s.label.isin([0, 1, 2, 3]).all():
            print(f"ERROR: la salida {k} no cubre exactamente el lote (faltan {len(ids - set(s.ID))}, sobran {len(set(s.ID) - ids)}, "
                  f"duplicados {int(s.ID.duplicated().sum())}, etiquetas inválidas {int((~s.label.isin([0, 1, 2, 3])).sum())})")
            return 2
        sal[k] = s.set_index("ID").label
    dif = lote[lote.ID.map(sal["a"]) != lote.ID.map(sal["b"])][["ID", "texto"]]
    dif.to_csv(x.salida, index=False, encoding="utf-8-sig")
    print(f"desacuerdos: {len(dif)} de {len(lote)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
