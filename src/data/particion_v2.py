# -*- coding: utf-8 -*-
"""Partición por hilos del dataset v2.0.0 (6 de noviembre de 2026). Regla fijada ANTES de entrenar y usando SOLO etiquetas:
- De los hilos de la ronda 3 (grupos A amenazas, B fútbol/humor/jerga, C política) se apartan 18 completos: 3 por grupo a val_hilos y 3 por grupo a test_hilos.
- Se prueban 20,000 asignaciones al azar (semilla 2026) y se elige la que minimiza la diferencia de proporciones de clase de cada mitad frente al total
  de la ronda 3, con al menos 120 Amenazas, 25 Odio y 300 Ofensivo por mitad.
- Las búsquedas de jerga (busqueda_*) son tuits independientes: se aparta el 30 % de cada búsqueda (estratificado por clase) y se reparte mitad y mitad.
- Para evaluar solo cuentan textos con consenso A = B (los dos anotadores ciegos coinciden). En train sigue la política RONDA3 con los hilos restantes.
Salida: data/dataset/particion_hilos.json"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src import paths as P  # noqa: E402

d = pd.read_csv(P.DATA / "annotation/threads/labels/consenso_ronda3.csv", encoding="utf-8-sig", dtype={"ID": str})
d = d[d.consenso >= 0]; d["ab"] = d.a == d.b
es_j = d.hilo.str.startswith("busqueda_"); h = d[~es_j & d.ab]
tab = h.groupby("hilo").agg(g=("grupo", "first"), **{f"c{c}": ("consenso", lambda s, c=c: int((s == c).sum())) for c in range(4)})
tab["g"] = tab.g.replace({"B2": "B"}); tot = tab[[f"c{c}" for c in range(4)]].sum(); ref = tot / tot.sum()
rng = np.random.default_rng(2026); mejor = None
for _ in range(20000):
    v, t = [], []
    for g, x in tab.groupby("g"):
        s = rng.choice(x.index.values, 6, replace=False); v += list(s[:3]); t += list(s[3:])
    cv, ct = tab.loc[v, ["c0", "c1", "c2", "c3"]].sum(), tab.loc[t, ["c0", "c1", "c2", "c3"]].sum()
    if min(cv.c3, ct.c3) < 120 or min(cv.c2, ct.c2) < 25 or min(cv.c1, ct.c1) < 300: continue
    err = float(np.abs(cv / cv.sum() - ref).sum() + np.abs(ct / ct.sum() - ref).sum())
    if mejor is None or err < mejor[0]: mejor = (err, sorted(v), sorted(t), cv.to_dict(), ct.to_dict())
err, val_h, test_h, cv, ct = mejor
j = d[es_j]; reserva = j.groupby(["hilo", "consenso"], group_keys=False).apply(lambda x: x.sample(frac=0.3, random_state=2026))
ids = reserva.ID.sample(frac=1, random_state=2026).tolist(); jv, jt = sorted(ids[: len(ids) // 2]), sorted(ids[len(ids) // 2:])
out = {"regla": __doc__.split("Salida")[0].strip(), "semilla": 2026, "error_proporciones": err,
       "val_hilos": val_h, "test_hilos": test_h, "jerga_val_ids": jv, "jerga_test_ids": jt,
       "conteos_AB": {"val_hilos": {k: int(v) for k, v in cv.items()}, "test_hilos": {k: int(v) for k, v in ct.items()}, "total_ronda3": {k: int(v) for k, v in tot.items()}}}
(P.DATASET / "particion_hilos.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: out[k] for k in ["error_proporciones", "val_hilos", "test_hilos", "conteos_AB"]}, ensure_ascii=False, indent=1), "jerga val/test", len(jv), len(jt))
