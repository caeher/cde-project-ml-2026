# -*- coding: utf-8 -*-
"""
Ensambla data/dataset_v3/.

train = reales de B2 + sintéticos de B2 + sintéticos V3, con el normalizador
corregido y sin ninguna fila que toque val, test o la batería adversarial.

val y test se copian TAL CUAL desde B2, byte por byte. No se re-normalizan ni se
reetiquetan. Es lo que mantiene comparables todas las métricas del proyecto
desde la v1, y lo que hace que nadie pueda acusar de haber movido la prueba.
"""
from __future__ import annotations
import hashlib, shutil, sys, unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar
from src.v3.augmentation_v3 import generar

B2 = RAIZ / "data/dataset_b2"
V3 = RAIZ / "data/dataset_v3"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def clave(s) -> str:
    return unicodedata.normalize("NFC", str(s)).strip().lower()


def leer(p):
    d = pd.read_csv(p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# Familias que atacan una debilidad MEDIDA en la sonda (amenazas ofuscadas,
# eufemismos, emojis, sesgo dialectal). Las que quedan fuera —el grueso de
# insultos ofuscados y de odio ofuscado— son 1,136 filas con la misma estructura
# repetida, y en esas familias los modelos ya acertaban entre el 68 % y el 89 %.
# Añadir volumen donde no hay problema solo desplaza la distribución de
# entrenamiento lejos de la natural.
FAMILIAS_DIRIGIDAS = {
    "v3_amenaza_ofuscada", "v3_amenaza_eufemismo",
    "v3_emoji_clase3", "v3_emoji_clase2", "v3_emoji_clase1", "v3_emoji_benigno",
    "v3_jerga_notoxico", "v3_jerga_control", "v3_jerga_ofensivo",
    "v3_nacionalidad_notoxico",
}


def main(dirigido: bool = False):
    V3.mkdir(exist_ok=True)

    # ── val y test: copia literal, sin tocar ─────────────────────────────
    for f in ["val.csv", "test.csv", "test_adversarial.csv", "lexicon_emojis.csv"]:
        shutil.copy2(B2 / f, V3 / f)
        assert sha(B2 / f) == sha(V3 / f)
    print("val / test / batería copiados sin modificar")

    val, test = leer(V3 / "val.csv"), leer(V3 / "test.csv")
    adv = leer(V3 / "test_adversarial.csv")

    # ── conjunto prohibido: todo lo que vive fuera del train ─────────────
    # La batería guarda su texto normalizado con el normalizador VIEJO. Tras
    # corregir el mapeo de 🔫 el mismo texto produce otra cadena, así que hay que
    # comparar también contra la normalización actual del texto crudo; si no, un
    # solape real pasa desapercibido. Es exactamente cómo se coló el de agosto.
    prohibido = ({clave(x) for x in val.texto_modelo} |
                 {clave(x) for x in test.texto_modelo} |
                 {clave(x) for x in adv.texto_normalizado} |
                 {clave(x) for x in adv.texto} |
                 {clave(normalizar(str(x))) for x in adv.texto} |
                 {clave(normalizar(str(x))) for x in val.texto_original} |
                 {clave(normalizar(str(x))) for x in test.texto_original})

    # La sonda de construcción es un conjunto de diagnóstico: si sus frases
    # entran al entrenamiento deja de medir generalización y pasa a medir
    # memorización, que es justo lo que este proyecto auditó en otros.
    from src.v3.sonda_construccion import BENIGNOS, AMENAZAS
    prohibido |= {clave(normalizar(t)) for t in BENIGNOS + AMENAZAS}

    # ── train de B2, re-normalizado con el normalizador corregido ────────
    tr = leer(B2 / "train.csv").copy()
    antes_txt = tr["texto_modelo"].tolist()
    tr["texto_modelo"] = [normalizar(t) for t in tr["texto_original"].astype(str)]
    n_renorm = sum(1 for a, b in zip(antes_txt, tr["texto_modelo"]) if a != b)

    # ── quitar el solape con la batería (las 7 filas de agosto) ──────────
    fuga = tr["texto_modelo"].map(clave).isin(prohibido)
    print(f"filas del train de B2 que tocaban val/test/batería: {int(fuga.sum())}")
    for t in tr.loc[fuga, "texto_modelo"].tolist():
        print(f"   fuera: {t[:70]}")
    tr = tr[~fuga].copy()

    # ── sintéticos V3 ────────────────────────────────────────────────────
    nuevos = generar()
    if dirigido:
        antes_n = len(nuevos)
        nuevos = nuevos[nuevos["origen"].isin(FAMILIAS_DIRIGIDAS)].reset_index(drop=True)
        print(f"subconjunto dirigido: {len(nuevos)} de {antes_n} sintéticos")
    nuevos["clase"] = [CLASES[i] for i in nuevos["label"]]
    nuevos["Plataforma"] = "sintetico"
    nuevos["texto_agresivo"] = ""
    nuevos["n_jerga"] = 0
    nuevos["Presencia_Sarcasmo"] = "NO"
    nuevos["Presencia_Ironia"] = "NO"
    nuevos["Contexto_Politico"] = "NO"

    cols = [c for c in tr.columns]
    for c in cols:
        if c not in nuevos.columns:
            nuevos[c] = "" if tr[c].dtype == object else 0
    nuevos["ID"] = nuevos["ID"] if "ID" in nuevos else ""
    nuevos = nuevos[cols]

    out = pd.concat([tr, nuevos], ignore_index=True)

    # ── deduplicar y volver a comprobar la higiene ───────────────────────
    antes = len(out)
    out = out.drop_duplicates(subset=["texto_modelo"]).reset_index(drop=True)
    dup = antes - len(out)
    resid = out["texto_modelo"].map(clave).isin(prohibido)
    assert not resid.any(), f"quedaron {int(resid.sum())} filas contaminadas"

    nombre = "train_dirigido.csv" if dirigido else "train.csv"
    out.to_csv(V3 / nombre, index=False, encoding="utf-8-sig")

    # ── metadatos ────────────────────────────────────────────────────────
    cnt = out["label"].value_counts().sort_index()
    pesos = [len(out) / (4 * cnt[i]) for i in range(4)]
    meta = {
        "n_train": len(out), "n_val": len(val), "n_test": len(test),
        "reales": int((out["origen"] == "real").sum()),
        "sinteticos_b2": int(out["origen"].astype(str).str.startswith("sintetico").sum()),
        "sinteticos_v3": int(out["origen"].astype(str).str.startswith("v3_").sum()),
        "por_clase": {CLASES[i]: int(cnt[i]) for i in range(4)},
        "pesos_clase": {CLASES[i]: round(pesos[i], 4) for i in range(4)},
        "renormalizadas": n_renorm, "duplicados_eliminados": dup,
        "solape_eliminado": int(fuga.sum()),
        "sha_val": sha(V3 / "val.csv"), "sha_test": sha(V3 / "test.csv"),
        "max_length": 128, "columna_texto": "texto_modelo",
        "normalizador": "normalize_for_model v1.2 (arroba y 🔫 corregidos)",
        "semilla": 42,
    }
    import json
    meta["dirigido"] = dirigido
    (V3 / ("metadata_dirigido.json" if dirigido else "metadata.json")).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False))

    print(f"\ntrain V3: {len(out)} filas")
    print(f"  reales        {meta['reales']:5d}")
    print(f"  sintéticos B2 {meta['sinteticos_b2']:5d}")
    print(f"  sintéticos V3 {meta['sinteticos_v3']:5d}")
    print(f"  re-normalizadas por el arreglo de la arroba/emoji: {n_renorm}")
    print(f"  duplicados eliminados: {dup}")
    print("\npor clase:")
    for i in range(4):
        print(f"  {CLASES[i]:20s} {cnt[i]:5d}   peso {pesos[i]:.4f}")
    print(f"\nval y test intactos: sha {meta['sha_val']} / {meta['sha_test']}")


if __name__ == "__main__":
    import sys
    main(dirigido="--dirigido" in sys.argv)
