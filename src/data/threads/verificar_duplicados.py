# -*- coding: utf-8 -*-
"""Verifica que textos nuevos (p. ej. una recolección de hilos) no estén repetidos en NINGÚN conjunto del proyecto.

Compara contra todos los CSV con columna de texto de data/, archivo/ (excepto los del propio --entrada):
  exacto      la misma clave de texto (minúsculas, sin URL, sin @, sin signos): build_dataset_final.clave
  normalizado el mismo texto tras src/features/normalization.normalizar (lo que ve el modelo)
  casi        similitud de Jaccard >= --umbral sobre 5-gramas de caracteres (reescrituras mínimas, emoji repetido, etc.)
Además revisa duplicados DENTRO del propio archivo de entrada.

Uso:
  .venv\\Scripts\\python.exe src/data/threads/verificar_duplicados.py --entrada data/sources/x_threads/phase3/*.csv
Salida: tabla en --salida (CSV) y resumen en pantalla. Código de salida 1 si hay algún duplicado (exacto, normalizado o casi).
"""
import argparse, glob, sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(RAIZ))
from src.data.build_dataset_final import clave  # noqa: E402
from src.features.normalization import normalizar  # noqa: E402
from src import paths as P  # noqa: E402

COLUMNAS_TEXTO = ["texto_original", "texto"]
K = 5  # tamaño de los shingles de caracteres
DF_MAX = 300  # shingles más comunes que esto no sirven para generar candidatos


def leer_textos(ruta):
    """Devuelve la lista de textos de un CSV, o [] si no tiene columna de texto."""
    try:
        d = pd.read_csv(ruta, encoding="utf-8-sig", dtype=str)
    except Exception:
        return []
    col = next((c for c in COLUMNAS_TEXTO if c in d.columns), None)
    return [] if col is None else d[col].dropna().tolist()


def shingles(texto):
    t = f" {clave(texto)} "
    return {t[i:i + K] for i in range(max(len(t) - K + 1, 1))}


def referencias(excluir):
    """Textos de todos los CSV del proyecto (una sola vez por clave), con su origen."""
    rutas = sorted(set(glob.glob(str(P.DATA / "**" / "*.csv"), recursive=True)) | set(glob.glob(str(RAIZ / "archivo" / "**" / "*.csv"), recursive=True)))
    rutas = [r for r in rutas if Path(r).resolve() not in excluir]
    ref = {}  # clave -> (texto, origen)
    for r in rutas:
        for t in leer_textos(r):
            k = clave(t)
            if k and k not in ref:
                ref[k] = (t, str(Path(r).relative_to(RAIZ)).replace("\\", "/"))
    return ref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", nargs="+", required=True, help="CSV con columna texto o texto_original")
    ap.add_argument("--salida", default="reports/improvement/verificacion_duplicados.csv")
    ap.add_argument("--umbral", type=float, default=0.8, help="Jaccard de 5-gramas a partir del cual se marca como casi duplicado")
    a = ap.parse_args()

    entrada = []
    for patron in a.entrada:
        for r in sorted(glob.glob(patron)) or [patron]:
            for t in leer_textos(r):
                entrada.append((t, str(Path(r).name)))
    if not entrada:
        print("No hay textos en la entrada (¿columna 'texto' o 'texto_original'?)."); return 1
    excluir = {Path(r).resolve() for p in a.entrada for r in (glob.glob(p) or [p])}
    ref = referencias(excluir)
    print(f"Entrada: {len(entrada)} textos · referencias únicas: {len(ref)} (de {len(glob.glob(str(P.DATA / '**' / '*.csv'), recursive=True))} CSV en data/)")

    filas, vistos = [], {}
    # 1. duplicados dentro de la entrada
    for i, (t, f) in enumerate(entrada, 1):
        k = clave(t)
        if k in vistos: filas.append(dict(i=i, entrada=f, tipo="interno exacto", J="", referencia="", texto=t[:90]))
        else: vistos[k] = i

    # 2. exacto y normalizado contra referencias
    norm_ref = {}
    for k, (t, origen) in ref.items(): norm_ref.setdefault(clave(normalizar(t)), (t, origen))
    for i, (t, f) in enumerate(entrada, 1):
        k = clave(t)
        if k in ref: filas.append(dict(i=i, entrada=f, tipo="exacto", J="1.00", referencia=ref[k][1], texto=t[:90])); continue
        kn = clave(normalizar(t))
        if kn in norm_ref: filas.append(dict(i=i, entrada=f, tipo="normalizado", J="1.00", referencia=norm_ref[kn][1], texto=t[:90]))

    # 3. casi duplicados: índice invertido de 5-gramas raros de las referencias
    idx = {}
    sh_ref = {}
    for k, (t, origen) in ref.items():
        s = shingles(t); sh_ref[k] = s
        for g in s: idx.setdefault(g, []).append(k)
    for i, (t, f) in enumerate(entrada, 1):
        s = shingles(t); cand = {}
        for g in s:
            lista = idx.get(g)
            if lista and len(lista) <= DF_MAX:
                for k in lista: cand[k] = cand.get(k, 0) + 1
        mejor = None
        for k, c in cand.items():
            if c < 3: continue
            j = len(s & sh_ref[k]) / len(s | sh_ref[k])
            if j >= a.umbral and (mejor is None or j > mejor[0]): mejor = (j, k)
        if mejor and not any(r["i"] == i for r in filas):
            filas.append(dict(i=i, entrada=f, tipo="casi", J=f"{mejor[0]:.2f}", referencia=ref[mejor[1]][1], texto=t[:90]))

    salida = RAIZ / a.salida; salida.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas, columns=["i", "entrada", "tipo", "J", "referencia", "texto"]).to_csv(salida, index=False, encoding="utf-8-sig")
    por_tipo = pd.Series([r["tipo"] for r in filas]).value_counts().to_dict() if filas else {}
    print(f"Duplicados: {len(filas)} {por_tipo}")
    print(f"Tabla: {salida.relative_to(RAIZ)}")
    return 1 if filas else 0


if __name__ == "__main__":
    sys.exit(main())
