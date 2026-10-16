# -*- coding: utf-8 -*-
"""Dataset v8 = v7 + hilos de Odio (consenso): lgbt_bandera, lgbt_ultimahora, racismo_orgullo.
RESERVADO ENTERO: xenofobia_federico (test de generalización de Odio por nacionalidad); también migrantes, externo 2 y militares.
Aborta si algún texto de train coincide (crudo o normalizado) con val, test, batería o cualquier externo."""
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
    H = RAIZ / "data/hilos_reales"; V7 = RAIZ / "data/dataset_v7"
    train = pd.read_csv(V7 / "train.csv"); c4 = pd.read_csv(H / "etiquetas/consenso_externo4.csv"); c4 = c4[c4.consenso >= 0]
    nuevo = c4[c4.hilo.isin(["lgbt_bandera", "lgbt_ultimahora", "racismo_orgullo"])]; reserv = c4[c4.hilo == "xenofobia_federico"]
    val, test, adv = (pd.read_csv(V7 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    mig, e2, mil = pd.read_csv(V7 / "externo_migrantes.csv"), pd.read_csv(V7 / "externo_2.csv"), pd.read_csv(V7 / "externo_militares.csv")
    prohibidas = claves(val.texto_original) | claves(test.texto_original) | claves(adv.texto) | claves(mig.texto_original) | claves(e2.texto_original) | claves(mil.texto_original) | claves(reserv.texto)
    choca = nuevo.texto.map(lambda t: bool(claves([t]) & prohibidas)); print("filas nuevas retiradas por coincidir con test/externos:", int(choca.sum()))
    nuevo = nuevo[~choca]
    filas = [{"ID": f"HR5-{i:04d}", "Plataforma": "X", "texto_original": r.texto, "texto_modelo": normalizar(r.texto), "texto_agresivo": normalizar_agresivo(r.texto),
              "clase": CLASES[int(r.consenso)], "label": int(r.consenso), "origen": "real_hilo", "plantilla_id": r.hilo, "validado": "CONSENSO"} for i, r in enumerate(nuevo.itertuples(), 1)]
    train = pd.concat([train, pd.DataFrame(filas)], ignore_index=True)
    kt = claves(train.texto_original)
    for n, t in {"val": val.texto_original, "test": test.texto_original, "bateria": adv.texto, "migrantes": mig.texto_original, "externo2": e2.texto_original, "militares": mil.texto_original, "xenofobia": reserv.texto}.items():
        s = kt & claves(t); assert not s, f"fuga train/{n}: {len(s)}"
    out = RAIZ / "data/dataset_v8"; out.mkdir(exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]: d.to_csv(out / f, index=False, encoding="utf-8")
    reserv.rename(columns={"texto": "texto_original", "consenso": "label"})[["ID", "hilo", "texto_original", "label"]].to_csv(out / "externo_xenofobia.csv", index=False, encoding="utf-8-sig")
    for n, d in [("externo_migrantes.csv", mig), ("externo_2.csv", e2), ("externo_militares.csv", mil)]: d.to_csv(out / n, index=False, encoding="utf-8-sig")
    meta = {"train_total": len(train), "filas_nuevas": len(nuevo), "nuevas_por_clase": {CLASES[k]: int(v) for k, v in nuevo.consenso.value_counts().sort_index().items()},
            "xenofobia_reservado": {CLASES[k]: int(v) for k, v in reserv.consenso.value_counts().sort_index().items()},
            "verificacion": "0 textos de train en val, test, batería ni externos (crudo y normalizado)"}
    json.dump(meta, open(out / "metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2); print(json.dumps(meta, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
