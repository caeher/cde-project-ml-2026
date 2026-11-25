# -*- coding: utf-8 -*-
"""
Normalizador: src/features/normalization.py v1.2 (el de la Etapa II).

Construye data/history/v1.3.1/ incorporando los 4,328 registros reales de X
recolectados el 7 de octubre de 2026 (data/sources/x_oct2026/).

Reglas:
  1. val y test NO se modifican (comparabilidad con todas las etapas).
  2. Ningún texto nuevo puede coincidir con val, test ni la batería adversarial.
  3. Textos duplicados entre anotadores con etiqueta distinta se excluyen.
  4. Se elimina URL_Original (dato personal re-identificable).
  5. Cada fila conserva su procedencia y una marca de "fuera de El Salvador",
     para poder excluirlas en una ablación sin reconstruir nada.
"""
import json, re, sys, unicodedata
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar, normalizar_agresivo, perfil_texto  # noqa: E402

B2 = RAIZ / "data/history/v1.1.0"          # val, test y batería: idénticos byte a byte a dataset_v3
BASE_E2 = RAIZ / "data/history/v1.2.0/train.csv"   # train de 6,416 de la Etapa II (repo v3, commit 95d3ba6)
NUEVOS = RAIZ / "data/sources/x_oct2026"
SALIDA = RAIZ / "data/history/v1.3.1"

ARCHIVOS = {"dataset_x2000.csv": "Willian", "lenguaje_ofensivo.csv": "Cristian", "thenewdata_X.csv": "Julio"}
MAPA = {"no tóxico": 0, "no toxico": 0, "lenguaje ofensivo": 1, "discurso de odio": 2,
        "amenazas/violencia": 3, "amenazas / violencia": 3}
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]

SV = r"\b(?:bukele|nayib|salvador\w*|cuscatl\w*|cipote|maje|cerote|chero|pisto|bicho|puchica|chivo|guanac\w*|marero\w*|fmln|arena)\b"
AJENO = (r"\b(?:petro|colombia\w*|uribe|m[eé]xico|mexican\w*|amlo|sheinbaum|plebit\w*|chingad\w*|pinche|maduro|venezol\w*|"
         r"milei|argentin\w*|kirchner|bullrich|macri|espa[ñn]a|psoe|gilipollas|co[ñn]o|boluarte|boric|chilen\w*)\b")


def clave(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"@\w+", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def cargar_nuevos() -> pd.DataFrame:
    partes = []
    for f, quien in ARCHIVOS.items():
        d = pd.read_csv(NUEVOS / f, encoding="utf-8-sig")
        d.columns = [c.strip().lstrip("﻿") for c in d.columns]
        d["fuente_archivo"] = f
        d["recolector"] = quien
        partes.append(d)
    return pd.concat(partes, ignore_index=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(BASE_E2),
                    help="train base; por defecto el de 6,416 de la Etapa II")
    ap.add_argument("--salida", default=str(SALIDA))
    args = ap.parse_args()
    global SALIDA_DIR
    SALIDA_DIR = Path(args.salida)
    log = {"train_base": str(Path(args.base).relative_to(RAIZ)) if Path(args.base).is_absolute() and RAIZ in Path(args.base).parents else args.base,
           "normalizador": "v1.2"}
    nuevos = cargar_nuevos()
    log["filas_recibidas"] = len(nuevos)

    nuevos["label"] = nuevos.Clase_Toxicidad.str.strip().str.lower().map(MAPA)
    sin_mapa = nuevos.label.isna().sum()
    assert sin_mapa == 0, f"{sin_mapa} filas con clase no reconocida"
    nuevos["label"] = nuevos.label.astype(int)
    nuevos["k"] = nuevos.Texto_Original.map(clave)

    # --- 0. Corrección según guía de anotación (§3.1, línea 70):
    #     "La afiliación política NO es categoría protegida" -> Lenguaje Ofensivo.
    pol = (nuevos.label == 2) & nuevos.Subclase_Toxicidad.astype(str).str.contains(
        r"discriminaci[oó]n pol[ií]tica|insulto pol[ií]tico", case=False, regex=True)
    log["reetiquetadas_politica_odio_a_ofensivo"] = int(pol.sum())
    nuevos.loc[pol, "label"] = 1
    nuevos.loc[pol, "Subclase_Toxicidad"] = "Descalificación Política"

    # --- 1. Fuga contra val / test / batería: se eliminan ---
    val, test = pd.read_csv(B2 / "val.csv"), pd.read_csv(B2 / "test.csv")
    adv = pd.read_csv(B2 / "test_adversarial.csv")
    prohibidas = set(val.texto_original.map(clave)) | set(test.texto_original.map(clave)) | set(adv.texto.map(clave))
    fuga = nuevos.k.isin(prohibidas)
    log["eliminadas_fuga_val_test_bateria"] = int(fuga.sum())
    nuevos[fuga][["fuente_archivo", "Texto_Original", "Clase_Toxicidad"]].to_csv(
        RAIZ / "reports/improvement/v4_filas_con_fuga.csv", index=False, encoding="utf-8-sig")
    nuevos = nuevos[~fuga]

    # --- 2. Conflictos de etiqueta entre anotadores: se excluyen y se reportan ---
    n_et = nuevos.groupby("k").label.nunique()
    conflicto = nuevos.k.isin(n_et[n_et > 1].index)
    log["eliminadas_conflicto_etiqueta"] = int(conflicto.sum())
    nuevos[conflicto][["fuente_archivo", "recolector", "Texto_Original", "Clase_Toxicidad"]].to_csv(
        RAIZ / "reports/improvement/v4_conflictos_etiqueta.csv", index=False, encoding="utf-8-sig")
    nuevos = nuevos[~conflicto]

    # --- 3. Duplicados internos y contra el train actual ---
    antes = len(nuevos)
    nuevos = nuevos.drop_duplicates("k")
    log["eliminadas_duplicado_interno"] = antes - len(nuevos)
    train = pd.read_csv(args.base)
    # Fuga heredada: filas del train B2 que coinciden con val/test bajo la clave estricta
    heredada = train.texto_original.map(clave).isin(prohibidas)
    log["eliminadas_fuga_heredada_train_base"] = int(heredada.sum())
    train = train[~heredada].copy()
    ya =nuevos.k.isin(set(train.texto_original.map(clave)))
    log["eliminadas_ya_en_train"] = int(ya.sum())
    nuevos = nuevos[~ya]
    nuevos = nuevos[nuevos.k.str.len() >= 3]

    # --- 4. Procedencia ---
    T = nuevos.Texto_Original.astype(str)
    nuevos["fuera_de_sv"] = T.str.contains(AJENO, case=False, regex=True) & ~T.str.contains(SV, case=False, regex=True)

    # --- 5. Al esquema del proyecto (sin URL_Original) ---
    filas = []
    for i, r in enumerate(nuevos.itertuples(index=False), start=1):
        txt = str(r.Texto_Original)
        p = perfil_texto(txt)
        filas.append({
            "ID": f"X26-{i:05d}", "Plataforma": "X",
            "fecha": getattr(r, "Fecha_Recolección", ""),
            "Usuario_ID_Anonimizado": r.Usuario_ID_Anonimizado,
            "texto_original": txt, "texto_modelo": normalizar(txt), "texto_agresivo": normalizar_agresivo(txt),
            "clase": CLASES[r.label], "label": r.label, "subclase": r.Subclase_Toxicidad,
            "Grupos_Afectados": r.Grupos_Afectados, "Presencia_Sarcasmo": r.Presencia_Sarcasmo,
            "Presencia_Ironia": r.Presencia_Ironia, "Contexto_Politico": r.Contexto_Politico,
            **{c: p.get(c) for c in ["n_chars", "n_palabras", "n_emojis", "n_menciones", "n_hashtags", "n_jerga"]},
            "origen": "real_x_oct2026", "plantilla_id": "",
            "recolector": r.recolector, "fuera_de_sv": bool(r.fuera_de_sv), "validado": "NO",
        })
    nv = pd.DataFrame(filas)

    for c, v in [("recolector", ""), ("fuera_de_sv", False), ("validado", "SI")]:
        if c not in train.columns:
            train[c] = v
    for c in nv.columns:
        if c not in train.columns:
            train[c] = ""
    v4 = pd.concat([train, nv], ignore_index=True)

    # --- 6. Verificación final: cero solape ---
    kv4 = set(v4.texto_original.map(clave)) | set(v4.texto_modelo.astype(str).map(clave))
    for nombre, textos in [("val", val.texto_original), ("test", test.texto_original), ("batería", adv.texto)]:
        k_eval = set(textos.map(clave)) | {clave(normalizar(str(t))) for t in textos}
        solape = kv4 & k_eval
        assert not solape, f"fuga con {nombre}: {len(solape)} textos"
    log["verificacion_solape"] = "0 textos de train en val, test o batería (texto crudo y normalizado)"

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    v4.to_csv(SALIDA_DIR / "train.csv", index=False, encoding="utf-8")
    val.to_csv(SALIDA_DIR / "val.csv", index=False, encoding="utf-8")
    test.to_csv(SALIDA_DIR / "test.csv", index=False, encoding="utf-8")
    adv.to_csv(SALIDA_DIR / "test_adversarial.csv", index=False, encoding="utf-8")

    cnt = v4.label.value_counts().sort_index()
    pesos = (len(v4) / (4 * cnt)).round(4).tolist()
    log.update({
        "nuevas_incorporadas": len(nv),
        "nuevas_fuera_de_sv": int(nv.fuera_de_sv.sum()),
        "train_v4_total": len(v4),
        "train_v4_reales": int(v4.origen.str.startswith("real").sum()),
        "train_v4_sinteticos": int((~v4.origen.str.startswith("real")).sum()),
        "distribucion_train_v4": {CLASES[k]: int(v) for k, v in cnt.items()},
        "nuevas_por_clase": {CLASES[k]: int(v) for k, v in nv.label.value_counts().sort_index().items()},
        "pesos_clase": pesos,
        "val_n": len(val), "test_n": len(test),
    })
    json.dump(log, open(SALIDA_DIR / "metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
