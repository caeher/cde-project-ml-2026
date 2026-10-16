# -*- coding: utf-8 -*-
"""Dataset v7 = v6 + hilos ricos en Amenazas (consenso): infierno_tierra y pandilleros_traslado.
RESERVADOS ENTEROS (nunca entrenan): militares_pandilleros (test de generalización de Amenazas), migrantes y externo 2.
Aborta si algún texto de train coincide (crudo o normalizado) con val, test, batería o cualquiera de los externos."""
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
    H = RAIZ / "data/hilos_reales"; V6 = RAIZ / "data/dataset_v6"
    train = pd.read_csv(V6 / "train.csv")
    c3 = pd.read_csv(H / "etiquetas/consenso_externo3.csv"); c3 = c3[c3.consenso >= 0]
    nuevo = c3[c3.hilo.isin(["infierno_tierra", "pandilleros_traslado"])]; reserv = c3[c3.hilo == "militares_pandilleros"]
    filas = [{"ID": f"HR4-{i:04d}", "Plataforma": "X", "texto_original": r.texto, "texto_modelo": normalizar(r.texto), "texto_agresivo": normalizar_agresivo(r.texto),
              "clase": CLASES[int(r.consenso)], "label": int(r.consenso), "origen": "real_hilo", "plantilla_id": r.hilo, "validado": "CONSENSO"} for i, r in enumerate(nuevo.itertuples(), 1)]
    train = pd.concat([train, pd.DataFrame(filas)], ignore_index=True)
    val, test, adv = (pd.read_csv(V6 / f) for f in ["val.csv", "test.csv", "test_adversarial.csv"])
    mig = pd.read_csv(H / "test_externo_migrantes.csv"); e2 = pd.read_csv(H / "etiquetas/consenso_externo2.csv"); e2 = e2[e2.consenso >= 0]
    kt = claves(train.texto_original)
    for n, t in {"val": val.texto_original, "test": test.texto_original, "bateria": adv.texto, "migrantes": mig.texto_original, "externo2": e2.texto, "militares": reserv.texto}.items():
        s = kt & claves(t); assert not s, f"fuga train/{n}: {len(s)}"
    out = RAIZ / "data/dataset_v7"; out.mkdir(exist_ok=True)
    train.to_csv(out / "train.csv", index=False, encoding="utf-8")
    for f, d in [("val.csv", val), ("test.csv", test), ("test_adversarial.csv", adv)]: d.to_csv(out / f, index=False, encoding="utf-8")
    reserv.rename(columns={"texto": "texto_original", "consenso": "label"})[["ID", "hilo", "texto_original", "label"]].to_csv(out / "externo_militares.csv", index=False, encoding="utf-8-sig")
    e2.rename(columns={"texto": "texto_original", "consenso": "label"})[["ID", "hilo", "texto_original", "label"]].to_csv(out / "externo_2.csv", index=False, encoding="utf-8-sig")
    mig.to_csv(out / "externo_migrantes.csv", index=False, encoding="utf-8-sig")
    meta = {"train_total": len(train), "filas_nuevas": len(nuevo), "nuevas_por_clase": {CLASES[k]: int(v) for k, v in nuevo.consenso.value_counts().sort_index().items()},
            "reservados": {"militares_pandilleros": len(reserv), "migrantes": len(mig), "externo2": len(e2)},
            "militares_por_clase": {CLASES[k]: int(v) for k, v in reserv.consenso.value_counts().sort_index().items()},
            "verificacion": "0 textos de train en val, test, batería ni externos (crudo y normalizado)"}
    json.dump(meta, open(out / "metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2); print(json.dumps(meta, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
