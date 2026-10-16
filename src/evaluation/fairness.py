# -*- coding: utf-8 -*-
"""Informe de sesgos y ética (plan de mejora, fase 5; rúbrica Etapa II: «Análisis de sesgos y ética», 15 pts).

Sobre el BANCO CONGELADO (data/banco_congelado/) y el test oficial, para un modelo o ensamble:
  1. Por plataforma (X vs Facebook) en el test oficial: F1-macro y recall por clase, con IC bootstrap.
  2. Por jerga salvadoreña vs sin jerga (test oficial, columna n_jerga): FPR sobre No Tóxico y recall de Odio.
  3. Por GRUPO OBJETIVO del discurso de odio (heurística por palabras clave; ver LIMITES): recall de Odio con IC y brecha máxima.
  4. Sobremarcado de menciones: de los textos No Tóxico que mencionan un grupo, qué fracción se clasifica como tóxica (por grupo).
  5. Por tema/hilo del banco (militares, xenofobia, migrantes, fútbol/política).
Cada tabla incluye n; los grupos con n < 20 se marcan como «sin potencia». IC bootstrap 95 % (2,000 remuestreos).
LIMITES (también escritos en el informe): grupos objetivo asignados por palabras clave (aprox.); etiquetas de consenso de anotadores LLM sin
validación humana; datos solo de X (Facebook solo en el test oficial); no se mide sesgo de autor/dialecto individual.

Uso: python src/evaluation/fairness.py --modelo v3.3.0
"""
import argparse, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd

RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.evaluation.comparar_v4 import f1m  # noqa: E402

CLASES = ["No Tóxico", "Ofensivo", "Odio", "Amenazas"]
GRUPOS = {  # orden de prioridad: el primero que coincide
    "LGBT": r"\bgays?\b|homosex|lesbian|\btrans\b|transex|transg|lgbt|marica|maricon|\bputos?\b|joto|travest|\bhomo\b",
    "mujeres/género": r"mujer|feminis|femin|\bviejas?\b|\bgordas?\b|marimach|machism|\bperras?\b|feminazi",
    "etnia/raza": r"\bindios?\b|\bnegros?\b|ind[ií]gena|cholo|racis|\bmoros?\b|gitan|\bblancos?\b|afro",
    "nacionalidad/migración": r"venezol|veneco|hondure|\bnicas?\b|nicarag|haiti|cuban|colombian|mexican|migrant|extranjer|musulm|[aá]rabe|\bchinos?\b|\bsudaca|inmigr|dominican|paragua",
}
PAT = {k: re.compile(v, re.I) for k, v in GRUPOS.items()}
JERGA = re.compile(r"\bcerote|\bmaje\b|\bvergon|\bverga\b|\bputa\b|chucho|\bcipote|pupusa|\bbicho\b|puchica|\bchivo\b|\bchero\b|guanaco|a huevo|\bpisto\b", re.I)


def grupo(t):
    for k, p in PAT.items():
        if p.search(str(t)): return k
    return "otro"


def ic(fn, y, p, n=2000, seed=1):
    r = np.random.default_rng(seed); v = []
    for _ in range(n):
        i = r.integers(0, len(y), len(y)); x = fn(y[i], p[i])
        if not np.isnan(x): v.append(x)
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if v else (np.nan, np.nan)


def rec(c): return lambda y, p: float((p[y == c] == c).mean()) if (y == c).any() else np.nan
def fpr(y, p): return float((p[y == 0] != 0).mean()) if (y == 0).any() else np.nan
def fmt(x, ci, n): return f"{x:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]" + ("  *sin potencia*" if n < 20 else "")


def probs_modelo(modelo, textos, etiqueta):
    from src.evaluation.combinar_modelos import probs_propio, cache
    man = RAIZ / "models" / modelo / "manifest.json"
    comp = json.loads(man.read_text(encoding="utf-8"))["componentes"] if man.exists() else [modelo]
    return np.mean([cache(f"{c}__{etiqueta}", lambda c=c: probs_propio(f"models/{c}", textos)) for c in comp], 0).argmax(1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--modelo", default="v3.3.0"); ap.add_argument("--salida", default="reports/fairness.md"); a = ap.parse_args()
    L = [f"# Informe de sesgos y ética — modelo {a.modelo}", "",
         "Generado por `src/evaluation/fairness.py` sobre el banco congelado y el test oficial. IC bootstrap 95 % entre corchetes; *sin potencia* = n < 20.", ""]
    # ---- datos
    te = pd.read_csv(RAIZ / "data/dataset_final/test.csv"); yt = te.label.values
    from src.evaluation.combinar_modelos import cache  # noqa: F401
    pt = probs_modelo(a.modelo, te.texto_original.tolist(), "test_oficial_fair")
    bk = [pd.read_csv(RAIZ / f"data/banco_congelado/{k}.csv").assign(banco=k) for k in ["migrantes", "externo2", "militares", "xenofobia"]]
    bk = pd.concat(bk, ignore_index=True); yb = bk.label.values; pb = probs_modelo(a.modelo, bk.texto_original.tolist(), "banco_fair")
    # ---- 0 resumen
    L += ["## 0. Resumen global", "", "| Conjunto | n | F1-macro [IC] | Recall NT / OF / OD / AM | FPR (NT) |", "|---|---|---|---|---|"]
    for nom, y, p in [("Test oficial", yt, pt), ("Banco congelado", yb, pb)]:
        f = f1m(y, p); lo, hi = ic(lambda yy, pp: f1m(yy, pp), y, p, n=800)
        L.append(f"| {nom} | {len(y)} | {f:.3f} [{lo:.3f}, {hi:.3f}] | " + " / ".join(f"{rec(c)(y, p):.2f}" for c in range(4)) + f" | {fpr(y, p):.3f} |")
    # ---- 1 plataforma
    L += ["", "## 1. Por plataforma (test oficial)", "", "| Plataforma | n | F1-macro [IC] | Recall Odio [IC] | Recall Amenazas [IC] | FPR NT [IC] |", "|---|---|---|---|---|---|"]
    res = {}
    for pl, g in te.groupby("Plataforma"):
        i = g.index.values; y, p = yt[i], pt[i]; f = f1m(y, p); lo, hi = ic(lambda yy, pp: f1m(yy, pp), y, p, n=800)
        L.append(f"| {pl} | {len(i)} | {f:.3f} [{lo:.3f}, {hi:.3f}] | {fmt(rec(2)(y, p), ic(rec(2), y, p), int((y == 2).sum()))} | {fmt(rec(3)(y, p), ic(rec(3), y, p), int((y == 3).sum()))} | {fmt(fpr(y, p), ic(fpr, y, p), int((y == 0).sum()))} |")
        res[pl] = f
    L.append(f"\nBrecha de F1-macro entre plataformas: **{max(res.values()) - min(res.values()):.3f}** ({max(res, key=res.get)} − {min(res, key=res.get)}).")
    # ---- 2 jerga
    L += ["", "## 2. Jerga salvadoreña (test oficial y banco)", "", "| Conjunto | Con jerga / sin jerga | n NT | FPR NT [IC] | n Odio | Recall Odio [IC] |", "|---|---|---|---|---|---|"]
    tj = te.n_jerga.fillna(0).values > 0
    for nom, y, p, mk in [("Test oficial", yt, pt, tj), ("Banco", yb, pb, np.array([bool(JERGA.search(str(t))) for t in bk.texto_original]))]:
        for et, m in [("con jerga", mk), ("sin jerga", ~mk)]:
            yy, pp = y[m], p[m]; n0, n2 = int((yy == 0).sum()), int((yy == 2).sum())
            L.append(f"| {nom} | {et} | {n0} | {fmt(fpr(yy, pp), ic(fpr, yy, pp), n0)} | {n2} | {fmt(rec(2)(yy, pp), ic(rec(2), yy, pp), n2)} |")
    # ---- 3 grupo objetivo (solo textos de Odio)
    L += ["", "## 3. Recall de Discurso de Odio por grupo objetivo (test oficial + banco; asignación por palabras clave)", "", "| Grupo objetivo | n Odio | Recall Odio [IC] | Clasificado como Ofensivo | Como No Tóxico |", "|---|---|---|---|---|"]
    y_all = np.concatenate([yt, yb]); p_all = np.concatenate([pt, pb]); tx_all = te.texto_original.tolist() + bk.texto_original.tolist(); g_all = np.array([grupo(t) for t in tx_all])
    rr = {}
    for gname in list(GRUPOS) + ["otro"]:
        m = (g_all == gname) & (y_all == 2); n = int(m.sum())
        if n == 0: continue
        y, p = y_all[m], p_all[m]; r = rec(2)(y, p); rr[gname] = (r, n)
        L.append(f"| {gname} | {n} | {fmt(r, ic(rec(2), y, p), n)} | {(p == 1).mean():.2f} | {(p == 0).mean():.2f} |")
    ok = {k: v[0] for k, v in rr.items() if v[1] >= 20 and k != "otro"}
    if len(ok) >= 2: L.append(f"\nBrecha máxima de recall de Odio entre grupos con n ≥ 20: **{max(ok.values()) - min(ok.values()):.3f}** ({max(ok, key=ok.get)} vs {min(ok, key=ok.get)}).")
    # ---- 4 sobremarcado
    L += ["", "## 4. Sobremarcado de menciones: textos **No Tóxico** que mencionan un grupo", "", "| Grupo mencionado | n (NT) | Marcados como tóxicos [IC] |", "|---|---|---|"]
    for gname in GRUPOS:
        m = (g_all == gname) & (y_all == 0); n = int(m.sum())
        if n == 0: continue
        y, p = y_all[m], p_all[m]; L.append(f"| {gname} | {n} | {fmt(fpr(y, p), ic(fpr, y, p), n)} |")
    # ---- 5 tema
    L += ["", "## 5. Por hilo / tema del banco", "", "| Banco | n | Acierto | Recall Odio | Recall Amenazas | FPR NT |", "|---|---|---|---|---|---|"]
    for k, g in bk.groupby("banco"):
        i = g.index.values; y, p = yb[i], pb[i]; L.append(f"| {k} | {len(i)} | {(y == p).mean():.3f} | {rec(2)(y, p):.2f} | {rec(3)(y, p):.2f} | {fpr(y, p):.3f} |")
    L += ["", "## Límites y advertencias éticas",
          "- Los grupos objetivo se asignan con palabras clave: un texto sobre «mujeres» y «migrantes» cae en el primer grupo que coincide; es aproximado.",
          "- Las etiquetas son consenso de anotadores LLM (Sonnet, Opus y un tercer modelo) **sin validación humana**: el sesgo de esos anotadores puede estar en las etiquetas y en el banco.",
          "- Los datos son de X (salvo la columna de plataforma del test oficial); no se evaluó dialecto individual ni autores.",
          "- El clasificador debe usarse como **apoyo a la moderación con revisión humana**, no como decisión automática: los errores se reparten de forma desigual por grupo (ver tablas) y una sanción errónea tiene costo real para quien la recibe."]
    out = RAIZ / a.salida; out.write_text("\n".join(L), encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
