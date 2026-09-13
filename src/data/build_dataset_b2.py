# -*- coding: utf-8 -*-
"""
Construye el dataset B2 a partir del v1 más los ejemplos sintéticos.

DECISIONES DE DISEÑO
--------------------
1. **Los sintéticos entran SOLO en `train`.** `val` y `test` quedan idénticos al
   v1, con datos 100% reales. Esto tiene dos consecuencias deseadas:
      - Las métricas de B2 son directamente comparables con las del v1: si el
        F1 sube, es porque el modelo mejoró, no porque el test se hizo más fácil.
      - No se inflan resultados con texto generado por plantilla, que es más
        predecible que el lenguaje real.

2. **Se añade un conjunto diagnóstico aparte** (`test_adversarial.csv`) con los
   casos de emoji, ofuscación y jerga. No sustituye al test: se reporta por
   separado como prueba de robustez.

3. Cada fila lleva `origen` y `plantilla_id`. Los sintéticos son filtrables con
   `df[df.origen == "real"]` para cualquier análisis que los deba excluir.

4. Deduplicación contra el corpus real y contra val/test, para descartar
   cualquier coincidencia accidental que produjera fuga.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sklearn.utils.class_weight import compute_class_weight  # noqa: E402

from src.data.augmentation import generar  # noqa: E402
from src.data.label_mapping import CLASES_CANONICAS, ID2LABEL, LABEL2ID  # noqa: E402
from src.data.lexicon_emojis import guardar as guardar_lexicon  # noqa: E402
from src.features.normalization import (normalizar, normalizar_agresivo,  # noqa: E402
                                        perfil_texto)

SEED = 42
V1 = ROOT / "data/processed"
B2 = ROOT / "data/dataset_b2"


def clave(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.normalize("NFKC").str.lower()
            .str.replace(r"\s+", " ", regex=True).str.strip())


def main():
    B2.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    # ---------------------------------------------------------- 1. Léxico
    lex = guardar_lexicon(str(ROOT / "data/raw/lexicon_emojis_v2.csv"))
    lex.to_csv(B2 / "lexicon_emojis.csv", index=False, encoding="utf-8-sig")
    print(f"[1] léxico de emojis reconstruido: {len(lex)} entradas")

    # ---------------------------------------------------------- 2. Base v1
    tr = pd.read_csv(V1 / "train.csv")
    va = pd.read_csv(V1 / "val.csv")
    te = pd.read_csv(V1 / "test.csv")
    for d in (tr, va, te):
        d["origen"] = "real"
        d["plantilla_id"] = ""
    print(f"[2] v1 -> train {len(tr)} | val {len(va)} | test {len(te)}")

    # ---------------------------------------------------------- 3. Sintéticos
    syn = generar(SEED)
    syn = syn.rename(columns={"subclase": "subclase_gold"})

    # Deduplicar contra TODO el corpus real (incluye val y test: evita fuga)
    reales = pd.concat([tr, va, te])
    k_real = set(clave(reales.texto_original))
    antes = len(syn)
    syn = syn[~clave(syn.texto).isin(k_real)].reset_index(drop=True)
    print(f"[3] sintéticos: {antes} generados, {antes-len(syn)} descartados por "
          f"coincidir con texto real -> {len(syn)}")

    # ---------------------------------------------------------- 4. Esquema
    syn["ID"] = [f"SYN-{i+1:04d}" for i in range(len(syn))]
    syn["texto_original"] = syn["texto"]
    syn["texto_modelo"] = syn["texto_original"].apply(normalizar)
    syn["texto_agresivo"] = syn["texto_original"].apply(normalizar_agresivo)
    syn["label"] = syn["clase"].map(LABEL2ID)
    syn["subclase"] = syn["subclase_gold"]
    syn["fecha"] = pd.NaT
    syn["Usuario_ID_Anonimizado"] = "SINTETICO"
    syn["Grupos_Afectados"] = "N/A"
    syn["Presencia_Sarcasmo"] = "NO"
    syn["Presencia_Ironia"] = "NO"
    syn["Contexto_Politico"] = "NO"

    perf = pd.DataFrame([perfil_texto(t) for t in syn.texto_original])
    for c in ["n_chars", "n_palabras", "n_emojis", "n_menciones", "n_hashtags"]:
        syn[c] = perf[c].values

    # Conteo de jerga con el mismo léxico que el v1
    lexs = pd.read_csv(ROOT / "data/raw/lexicon_salvadoreno.csv", dtype=str)
    terms = {t for t in lexs.Texto_Original.astype(str).str.lower().str.strip() if len(t) > 2}
    import re
    syn["n_jerga"] = syn.texto_original.apply(
        lambda s: len(set(re.findall(r"\w+", str(s).lower())) & terms))

    COLS = list(tr.columns)
    syn = syn[COLS]

    # ---------------------------------------------------------- 5. Unir
    tr_b2 = pd.concat([tr, syn], ignore_index=True)
    tr_b2 = tr_b2.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Verificación de fuga
    assert not (set(clave(tr_b2.texto_original)) & set(clave(te.texto_original))), "fuga train-test"
    assert not (set(clave(tr_b2.texto_original)) & set(clave(va.texto_original))), "fuga train-val"
    assert tr_b2.texto_original.duplicated().sum() == 0, "duplicados en train"

    print(f"[4] train B2: {len(tr_b2)} ({len(tr)} reales + {len(syn)} sintéticos)")

    # ---------------------------------------------------------- 6. Diagnóstico
    sys.path.insert(0, str(ROOT / "src/audit"))
    from adversarial import CASOS  # noqa: E402
    adv = pd.DataFrame(CASOS)
    adv["ID"] = [f"ADV-{i+1:04d}" for i in range(len(adv))]
    adv["clase"] = adv.esperado.map(ID2LABEL)
    adv["label"] = adv.esperado
    adv["texto_original"] = adv.texto
    adv["texto_modelo"] = adv.texto_original.apply(normalizar)
    adv = adv[["ID", "grupo", "base", "variante", "texto_original", "texto_modelo",
               "clase", "label"]]
    adv.to_csv(B2 / "test_adversarial.csv", index=False, encoding="utf-8-sig")
    print(f"[5] conjunto diagnóstico adversarial: {len(adv)} casos")

    # ---------------------------------------------------------- 7. Guardar
    for nom, d in [("train", tr_b2), ("val", va), ("test", te)]:
        d.to_csv(B2 / f"{nom}.csv", index=False, encoding="utf-8-sig")
    pd.concat([tr_b2, va, te], ignore_index=True).to_csv(
        B2 / "corpus_completo.csv", index=False, encoding="utf-8-sig")

    pesos = compute_class_weight("balanced", classes=np.arange(4), y=tr_b2.label.values)
    pesos_d = {ID2LABEL[i]: round(float(w), 4) for i, w in enumerate(pesos)}

    import emoji as _emo
    def con_emoji(d):
        return int((d.texto_original.astype(str).apply(_emo.emoji_count) > 0).sum())

    meta = {
        "version": "b2",
        "generado": pd.Timestamp.now().isoformat(timespec="seconds"),
        "semilla": SEED,
        "base": "dataset v1 (3,063 reales) + aumento sintético dirigido",
        "totales": {"train": len(tr_b2), "val": len(va), "test": len(te)},
        "composicion_train": {
            "reales": int(len(tr)),
            "sinteticos": int(len(syn)),
            "por_origen": syn.origen.value_counts().to_dict(),
        },
        "distribucion_train": tr_b2.clase.value_counts().to_dict(),
        "emojis": {
            "train_con_emoji": con_emoji(tr_b2),
            "train_con_emoji_v1": con_emoji(tr),
            "por_clase": {c: con_emoji(tr_b2[tr_b2.clase == c]) for c in CLASES_CANONICAS},
        },
        "pesos_clase": pesos_d,
        "campo_texto": "texto_modelo",
        "reglas": [
            "Los sintéticos están solo en train; val y test son 100% reales e idénticos al v1",
            "Las métricas de B2 son comparables con las del v1 porque el test no cambió",
            "Filtrar con df[df.origen=='real'] para excluir sintéticos de cualquier análisis",
            "test_adversarial.csv es diagnóstico: se reporta aparte, nunca como métrica principal",
        ],
        "correcciones_incluidas": [
            "Catálogo de emojis reconstruido (glifos perdidos por codificación cp850)",
            "Cobertura de emoji equilibrada entre las cuatro clases",
            "Amenazas con ofuscación leetspeak y eufemismos salvadoreños",
            "No tóxicos con jerga salvadoreña, contra el sesgo dialectal",
            "No tóxicos mencionando nacionalidades, contra el sobreetiquetado de odio",
        ],
    }
    with open(B2 / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[6] guardado en data/dataset_b2/")
    print(f"    distribución train: {tr_b2.clase.value_counts().to_dict()}")
    print(f"    train con emoji: {con_emoji(tr)} -> {con_emoji(tr_b2)}")
    print(f"    pesos de clase: {pesos_d}")
    return meta


if __name__ == "__main__":
    main()
