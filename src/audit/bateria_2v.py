# -*- coding: utf-8 -*-
"""Batería adversarial de 144 casos sobre los cuatro checkpoints."""
import json
from pathlib import Path
import numpy as np, pandas as pd

RAIZ = Path("/home/willian/ues/esp/proyecto"); S = RAIZ / "reports/v2_auditoria"
MODS = ["mbert_v1", "mbert_b2", "xlmr_v1", "xlmr_mit"]
CL = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]

adv = pd.read_csv(RAIZ / "data/dataset_b2/test_adversarial.csv")
adv.columns = [c.lstrip("﻿") for c in adv.columns]
y = adv["label_esperado"].values

tab, res = {}, {}
for m in MODS:
    yp = np.load(S / f"logits_{m}_adv.npy").argmax(1)
    adv[f"pred_{m}"] = yp
    ok = (yp == y)
    res[m] = {"global": f"{ok.sum()}/{len(y)}", "aciertos": int(ok.sum())}
    for g, sub in adv.groupby("grupo_de_prueba"):
        k = sub.index.values
        res[m][g] = {"n": len(k), "aciertos": int(ok[k].sum())}
    # FPR sobre los grupos de sólo-negativos
    for g in ["D. Jerga salvadoreña inofensiva", "E. Control sin jerga"]:
        sub = adv[adv.grupo_de_prueba == g]
        res[m][g]["fpr"] = float((sub[f"pred_{m}"] != 0).mean())

print(f"{'grupo':34s}" + "".join(f"{m:>12s}" for m in MODS))
for g in sorted(adv.grupo_de_prueba.unique()):
    n = res[MODS[0]][g]["n"]
    print(f"{g:30s} n={n:<3d}" + "".join(f"{res[m][g]['aciertos']:>7d}/{n:<4d}" for m in MODS))
print(f"{'GLOBAL':30s} n=144" + "".join(f"{res[m]['aciertos']:>7d}/144 " for m in MODS))

print("\nBrecha FPR dialectal (D − E):")
for m in MODS:
    d = res[m]["D. Jerga salvadoreña inofensiva"]["fpr"]; e = res[m]["E. Control sin jerga"]["fpr"]
    res[m]["brecha_D_E"] = d - e
    print(f"  {m:10s} D={d:.4f}  E={e:.4f}  brecha={d-e:+.4f}")

# subconjunto de 75 (los grupos A-D del diseño original)
g75 = adv[adv.grupo_de_prueba.str[0].isin(list("ABCD"))]
print(f"\nSubconjunto A–D (n={len(g75)}):")
for m in MODS:
    print(f"  {m:10s} {(g75[f'pred_{m}'].values == g75['label_esperado'].values).sum()}/{len(g75)}")

adv.to_csv(S / "bateria_predicciones.csv", index=False, encoding="utf-8-sig")
(S / "bateria_resultados.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

# Detalle de amenazas ofuscadas y ofuscación de groserías
print("\n--- C. Amenazas ofuscadas: detalle ---")
c = adv[adv.grupo_de_prueba.str.startswith("C.")]
for _, r in c.iterrows():
    print(f"  {r['texto'][:44]:46s}" + "".join(f" {CL[r[f'pred_{m}']][:6]:>7s}" for m in MODS))
print("\n--- A. Ofuscación de groserías: detalle ---")
a = adv[adv.grupo_de_prueba.str.startswith("A.")]
for _, r in a.iterrows():
    print(f"  {r['variante']:12s} {r['texto'][:34]:36s}" + "".join(f" {CL[r[f'pred_{m}']][:6]:>7s}" for m in MODS))
