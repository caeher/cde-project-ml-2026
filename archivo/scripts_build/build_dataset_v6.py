# -*- coding: utf-8 -*-
"""Dataset v6: base de v5f SIN las filas de hilos con mis etiquetas, más TODOS los hilos con etiquetas de CONSENSO.

Etiquetas de hilos = consenso de anotadores independientes (guía v2.0):
  - 6 hilos (1,155 textos): Claude + agente ciego (+ tercer agente si discrepan). Mayoría de 2 de 3.
  - 3 hilos nuevos (trans, racismo, venezolanos2): dos agentes ciegos (+ tercero si discrepan).
  - Sin mayoría → el texto se EXCLUYE.
Reservado ENTERO como test externo (nunca entra a train): hilo de migrantes (Chile).
Se conservan los 88 casos difíciles (origen caso_dificil). Peso de todo lo nuevo: 1.0 (en entrenar_v5.py --peso_hilos).
Aborta si algún texto de train coincide (crudo o normalizado) con val, test, batería o el test externo.
"""
import json, re, sys, unicodedata
from pathlib import Path
import pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar, normalizar_agresivo  # noqa: E402
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]


def clave(s):
    s = unicodedata.normalize("NFKC", str(s)).lower(); s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"@\w+", " ", s); s = re.sub(r"[^\w\s]", " ", s); return re.sub(r"\s+", " ", s).strip()


def claves(t): return set(map(clave, t)) | {clave(normalizar(str(x))) for x in t}


def main():
    V5 = RAIZ / "data/dataset_v5f"; H = RAIZ / "data/hilos_reales"
    train = pd.read_csv(V5 / "train.csv"); train = train[train.origen != "real_hilo"].copy()
    c1 = pd.read_csv(H / "etiquetas/consenso_1155.csv"); c1 = c1[c1.consenso >= 0][["hilo", "texto_original", "consenso"]]
    c2 = pd.read_csv(H / "etiquetas/consenso_nuevos.csv"); c2 = c2[c2.consenso >= 0][["hilo", "texto", "consenso"]].rename(columns={"texto": "texto_original"})
    nuevos = pd.concat([c1, c2], ignore_index=True)
    filas = [{"ID": f"HR3-{i:04d}", "Plataforma": "X", "texto_original": r.texto_original, "texto_modelo": normalizar(r.texto_original),
              "texto_agresivo": normalizar_agresivo(r.texto_original), "clase": CLASES[int(r.consenso)], "label": int(r.consenso),
              "origen": "real_hilo", "plantilla_id": r.hilo, "validado": "CONSENSO"} for i, r in enumerate(nuevos.itertuples(), 1)]
    train = pd.concat([train, pd.DataFrame(filas)], ignore_index=True)
    val, test, adv = (pd.read_csv(V5 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    ext = pd.read_csv(H / "test_externo_migrantes.csv")
    kt = claves(train.texto_original)
    for n, t in {"val": val.texto_original, "test": test.texto_original, "bateria": adv.texto, "test_externo_migrantes": ext.texto_original}.items():
        s = kt & claves(t); assert not s, f"fuga train/{n}: {len(s)}"
    out = RAIZ / "data/dataset_v6"; out.mkdir(exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]: d.to_csv(out / f, index=False, encoding="utf-8")
    ext.to_csv(out / "externo_migrantes.csv", index=False, encoding="utf-8-sig")
    meta = {"train_total": len(train), "base_sin_hilos": int((train.origen != "real_hilo").sum()), "filas_hilos_consenso": len(nuevos),
            "hilos_en_train": sorted(nuevos.hilo.unique().tolist()), "externo_migrantes": len(ext),
            "distribucion_hilos": {CLASES[k]: int(v) for k, v in nuevos.consenso.value_counts().sort_index().items()},
            "distribucion_train": {CLASES[k]: int(v) for k, v in train.label.value_counts().sort_index().items()},
            "verificacion": "0 textos de train en val, test, batería ni test externo (crudo y normalizado)"}
    json.dump(meta, open(out / "metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2); print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
