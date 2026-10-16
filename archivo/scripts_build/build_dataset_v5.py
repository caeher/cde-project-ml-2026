# -*- coding: utf-8 -*-
"""Dataset v5: base sin octubre + hilos reales etiquetados + casos difíciles (pares mínimos).

Dos variantes, para poder medir generalización sin contaminar:
  A  (experimento):  entrena con hilos {repatriados, invasion}; RESERVA {canje, feminismo} completos
                     y los pares de casos difíciles d..g (probe). val/test/batería no cambian.
  F  (final):        entrena con todos los hilos y todos los casos difíciles.

Controles (abortan si fallan): cero solape de texto (crudo y normalizado) entre train y
val / test / batería / hilos reservados / casos de probe.
Normalizador: src/features/normalization.py v1.2 (el mismo del entrenamiento y la API).
"""
import json, re, sys, unicodedata
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar, normalizar_agresivo  # noqa: E402

V4 = RAIZ / "data/dataset_v4"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
HILOS_TRAIN_A = ["repatriados", "invasion"]
HILOS_HELD_A = ["canje", "feminismo"]
PARES_TRAIN_A = list("abc")


def clave(s):
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"https?://\S+", " ", s); s = re.sub(r"@\w+", " ", s); s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def filas(df, origen, prefijo):
    out = []
    for i, r in enumerate(df.itertuples(index=False), 1):
        t = str(r.texto)
        out.append({"ID": f"{prefijo}-{i:04d}", "Plataforma": "X", "texto_original": t,
                    "texto_modelo": normalizar(t), "texto_agresivo": normalizar_agresivo(t),
                    "clase": CLASES[int(r.label)], "label": int(r.label), "origen": origen,
                    "plantilla_id": getattr(r, "grupo", ""), "validado": "NO"})
    return pd.DataFrame(out)


def claves(textos):
    return set(map(clave, textos)) | {clave(normalizar(str(t))) for t in textos}


def construir(nombre, hilos_train, hilos_held, pares_train, hilos, hard):
    base = pd.read_csv(V4 / "train.csv")
    base = base[base.origen != "real_x_oct2026"].copy()
    val, test, adv = (pd.read_csv(V4 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    h_tr = hilos[hilos.hilo.isin(hilos_train)].rename(columns={"texto_original": "texto"})
    h_held = hilos[hilos.hilo.isin(hilos_held)]
    c_tr = hard[hard.par.isin(pares_train)]
    c_probe = hard[~hard.par.isin(pares_train)]
    nuevo = pd.concat([filas(h_tr, "real_hilo", "HR"), filas(c_tr, "caso_dificil", "CD")], ignore_index=True)
    train = pd.concat([base, nuevo], ignore_index=True)

    k_train = claves(train.texto_original)
    prohibidos = {"val": val.texto_original, "test": test.texto_original, "bateria": adv.texto,
                  "hilos_reservados": h_held.texto_original, "casos_probe": c_probe.texto}
    for n, t in prohibidos.items():
        s = k_train & claves(t)
        assert not s, f"[{nombre}] fuga train/{n}: {len(s)} textos, p. ej. {list(s)[:2]}"
    out = RAIZ / "data" / nombre; out.mkdir(parents=True, exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]:
        d.to_csv(out / f, index=False, encoding="utf-8")
    if len(h_held):
        h_held.to_csv(out / "hilos_reservados.csv", index=False, encoding="utf-8-sig")
    if len(c_probe):
        c_probe.to_csv(out / "casos_probe.csv", index=False, encoding="utf-8-sig")
    cnt = train.label.value_counts().sort_index()
    meta = {"nombre": nombre, "train_total": len(train), "base_sin_octubre": len(base),
            "hilos_train": hilos_train, "hilos_reservados": hilos_held,
            "filas_hilos_train": len(h_tr), "filas_casos_train": len(c_tr),
            "filas_hilos_reservados": len(h_held), "filas_casos_probe": len(c_probe),
            "distribucion": {CLASES[k]: int(v) for k, v in cnt.items()},
            "verificacion": "0 textos de train en val, test, batería, hilos reservados ni casos probe (crudo y normalizado)"}
    json.dump(meta, open(out / "metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


def main():
    hilos = pd.read_csv(RAIZ / "data/hilos_reales/hilos_etiquetados.csv")
    hard = pd.read_csv(RAIZ / "data/hard_cases/casos_dificiles.csv")
    construir("dataset_v5a", HILOS_TRAIN_A, HILOS_HELD_A, PARES_TRAIN_A, hilos, hard)
    construir("dataset_v5f", list(hilos.hilo.unique()), [], list("abcdefg"), hilos, hard)


if __name__ == "__main__":
    main()
