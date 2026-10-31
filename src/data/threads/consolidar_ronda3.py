# -*- coding: utf-8 -*-
"""Consolida la ronda 3: textos recolectados + anotación a ciegas (A y B en todos los lotes; C solo desempata sus desacuerdos).

Cada archivo de anotación se valida (ID del lote, etiqueta 0–3, sin repetidos) y se usan los textos que tienen etiqueta de A **y** de B,
aunque el lote haya quedado incompleto. Estado por texto:
  consenso            A = B
  consenso_c          A ≠ B y C coincide con uno de los dos (mayoría de 3)
  sin_consenso        A, B y C distintos
  desacuerdo_pendiente A ≠ B y C todavía no lo resolvió
  un_anotador         solo hay etiqueta de A o de B
  sin_anotar          ninguna etiqueta (incluye todos los textos de jerga, que no pasaron por anotación)
Salidas:
  data/annotation/threads/labels/ronda3_consolidado.csv   todos los textos y su estado
  data/annotation/threads/labels/consenso_ronda3.csv      solo los que ya tienen consenso (ID,hilo,grupo,subgrupo,texto,a,b,d,consenso)
  reports/improvement/consolidado_ronda3.md               resumen con cifras
Uso: python src/data/threads/consolidar_ronda3.py
"""
import glob, os, re, sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

RAIZ = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402

B = P.THREADS / "blind" / "ronda3"
CLASES = ["No Tóxico", "Ofensivo", "Odio", "Amenazas"]
JERGA = re.compile(r"\bcerote|\bmaje\b|\bvergon|\bvergón|\bverga\b|\bputa\b|chucho|\bcipote|pupusa|\bbicho\b|puchica|púchica|\bchivo\b|\bchero\b|guanaco|a huevo|\bpisto\b|\bbayunco|\bchambre|\bpaja\b|\bcuilio|\bchele\b|\bachís|\bachis\b|cachimb|\bjaña|\bjana\b|\bchulon|\bchulón", re.I)


def leer(f):
    return pd.read_csv(f, encoding="utf-8-sig", dtype={"ID": str})


def etiquetas(lote_ids, ruta):
    """Etiquetas válidas de un archivo de anotación (ID del lote, 0–3, una por ID); {} si el archivo no existe."""
    if not os.path.exists(ruta): return {}
    s = pd.read_csv(ruta, dtype={"ID": str})
    s = s[s.ID.isin(lote_ids) & s.label.isin([0, 1, 2, 3])].drop_duplicates("ID", keep="first")
    return dict(zip(s.ID, s.label.astype(int)))


def main():
    p3 = pd.concat([leer(f) for f in sorted(glob.glob(str(P.X_THREADS / "phase3" / "*.csv")))], ignore_index=True)
    pj = pd.concat([leer(f) for f in sorted(glob.glob(str(P.X_THREADS / "phase3_jerga" / "*.csv")))], ignore_index=True)
    base = pd.concat([p3.assign(origen="phase3"), pj.assign(origen="jerga")], ignore_index=True)[["ID", "hilo", "grupo", "subgrupo", "texto", "origen"]]
    assert not base.ID.duplicated().any(), "IDs repetidos entre phase3 y jerga"

    a, b, c, lote_de = {}, {}, {}, {}
    for f in sorted(glob.glob(str(B / "lote_R3*.csv"))):
        lote = re.sub(r"^lote_", "", Path(f).stem); ids = set(leer(f).ID)
        if not re.match(r"R3[ABC]_", lote):  # los lotes de rescate (R3A/R3B: texto sin A o sin B; R3C: desempate) no cambian el lote de origen del texto
            for i in ids: lote_de[i] = lote
        a.update(etiquetas(ids, B / f"salida_{lote}a.csv")); b.update(etiquetas(ids, B / f"salida_{lote}b.csv")); c.update(etiquetas(ids, B / f"salida_{lote}c.csv"))
    d = base.copy()
    d["lote"] = d.ID.map(lote_de)
    d["a"], d["b"], d["d"] = d.ID.map(a), d.ID.map(b), d.ID.map(c)

    def estado(r):
        if pd.isna(r.a) and pd.isna(r.b): return "sin_anotar", None
        if pd.isna(r.a) or pd.isna(r.b): return "un_anotador", None
        if r.a == r.b: return "consenso", int(r.a)
        if pd.isna(r.d): return "desacuerdo_pendiente", None
        if int(r.d) in (int(r.a), int(r.b)): return "consenso_c", int(r.d)
        return "sin_consenso", None
    est = d.apply(estado, axis=1)
    d["estado"] = est.map(lambda t: t[0]); d["consenso"] = est.map(lambda t: t[1]).astype("Int64")
    for k in "abd": d[k] = d[k].astype("Int64")

    destino = P.THREAD_LABELS / "ronda3_consolidado.csv"
    d[["ID", "origen", "hilo", "grupo", "subgrupo", "lote", "texto", "a", "b", "d", "consenso", "estado"]].sort_values("ID").to_csv(destino, index=False, encoding="utf-8-sig")
    ok = d[d.consenso.notna()]
    ok[["ID", "hilo", "grupo", "subgrupo", "texto", "a", "b", "d", "consenso"]].sort_values("ID").to_csv(P.THREAD_LABELS / "consenso_ronda3.csv", index=False, encoding="utf-8-sig")

    par = d[d.a.notna() & d.b.notna()]
    kappa = cohen_kappa_score(par.a.astype(int), par.b.astype(int))
    por_lote = par.groupby("lote").apply(lambda g: (g.a == g.b).mean(), include_groups=False)
    L = ["# Consolidado de la ronda 3 (anotación a ciegas)", "",
         "Generado por `src/data/threads/consolidar_ronda3.py`. Textos recolectados con BrowserOS (respuestas públicas de X, sin usuarios); etiquetas de agentes Haiku 5.5 con la guía v2.0: "
         "A lee la guía completa, B trabaja con un resumen; C desempata a ciegas solo los desacuerdos. **Todos los anotadores son LLM del mismo modelo: errores correlacionados, sin validación humana.**", "",
         "## Estado de los textos", "", "| Estado | Textos |", "|---|---|"]
    for k, v in d.estado.value_counts().items(): L.append(f"| {k} | {v:,} |")
    L += ["", f"Total: **{len(d):,}** textos ({(d.origen == 'phase3').sum():,} de hilos de la ronda 3 y {(d.origen == 'jerga').sum():,} de la búsqueda de jerga).", "",
          f"## Acuerdo entre A y B ({len(par):,} textos con las dos etiquetas)", "",
          f"- κ de Cohen = **{kappa:.3f}** (umbral de la guía: 0.60); acuerdo = {(par.a == par.b).mean():.3f}.",
          f"- Acuerdo por lote: mínimo {por_lote.min():.3f}, mediana {por_lote.median():.3f}, máximo {por_lote.max():.3f}."]
    for i, n in enumerate(CLASES): L.append(f"- κ de la clase {n}: {cohen_kappa_score(par.a.astype(int) == i, par.b.astype(int) == i):.3f}")
    L += ["", "## Textos con consenso por grupo y clase", "", "| Grupo | " + " | ".join(CLASES) + " | Total |", "|---|" + "---|" * 5]
    for g, sub in ok.groupby("grupo"):
        L.append(f"| {g} | " + " | ".join(f"{int((sub.consenso == i).sum()):,}" for i in range(4)) + f" | {len(sub):,} |")
    L.append("| **Total** | " + " | ".join(f"**{int((ok.consenso == i).sum()):,}**" for i in range(4)) + f" | **{len(ok):,}** |")
    nt_j = ok[(ok.consenso == 0) & ok.texto.str.contains(JERGA)]; of_j = ok[(ok.consenso == 1) & ok.texto.str.contains(JERGA)]
    L += ["", f"Con jerga (léxico amplio, `JERGA` en el script): **{len(nt_j):,}** No Tóxico y **{len(of_j):,}** Ofensivo con consenso. "
              "El plan de la ronda 3 pedía ≥ 300 No Tóxico con jerga; el léxico amplio incluye términos que también se usan fuera de El Salvador.", "",
          "## Lotes y desempate", "",
          f"- Lotes de origen con A y B completos: {int((d.dropna(subset=['lote']).groupby('lote').apply(lambda g: g.a.notna().all() and g.b.notna().all(), include_groups=False)).sum())} de {d.lote.nunique()}; el resto se completó con lotes de rescate (`lote_R3A_*`, `lote_R3B_*`).",
          f"- Desempatados por C: {int(d.d.notna().sum()):,} textos. Pendientes de desempate: {int((d.estado == 'desacuerdo_pendiente').sum()):,}. Sin consenso (A, B y C distintos): {int((d.estado == 'sin_consenso').sum()):,}, que no se usan.",
          f"- C marcó seguro=0 en la mayoría de los desacuerdos (son los casos más difíciles): las etiquetas de `consenso_c` son más ruidosas; en el dataset llevan etiqueta blanda (2 de 3 votos).", "",
          "## Advertencias", "",
          "- **La jerga recolectada es poca y de calidad dudosa:** 470 textos en 8 términos, 57 % de un solo término («achis»), con contenido de México y España y nombres propios («jana», «chulón»). "
          "En el dataset v1.9.0 se excluyen los marcados `pais_dudoso=1` y los textos con marcas de México o España, y «achis» se limita a 80 textos (`RONDA3` en `src/data/build_dataset_final.py`).",
          "- Los textos sin consenso quedan fuera; excluirlos sesga la muestra hacia lo fácil.",
          "- Los anotadores son del mismo modelo (Haiku 5.5): errores correlacionados y sin validación humana.",
          "- El dataset v1.9.0 incorpora estas etiquetas con la política de balance `RONDA3` (todas las Amenazas y el Odio; tope por hilo de No Tóxico y Ofensivo). El banco congelado y el conjunto de val y test no cambian.", ""]
    (P.REPORTS_IMPROVEMENT / "consolidado_ronda3.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
