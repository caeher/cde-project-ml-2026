# -*- coding: utf-8 -*-
"""
Reejecución independiente de los modelos de la entrega 2v.

Carga cada checkpoint entregado, corre el forward pass sobre test.csv y sobre
la batería adversarial de 144 casos, y guarda logits + predicciones.

Contrato: max_length=128, columna texto_modelo, semilla 42.
"""
import json, sys, hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

RAIZ = Path("/home/willian/ues/esp/proyecto")
EXTR = RAIZ / "Métricas de Evaluación/2v/_extraido"
SALIDA = RAIZ / "reports/v2_auditoria"
SALIDA.mkdir(parents=True, exist_ok=True)

MODELOS = {
    "mbert_b2":  EXTR / "metricas-proyecto-ml/models/mbert-sv",
    "mbert_v1":  EXTR / "mbert_v1/mbert-sv",
    "xlmr_v1":   RAIZ / "Métricas de Evaluación/Para modelo XLMR/02_modelo_prototipo/modelo_entrenado",
    "xlmr_mit":  EXTR / "prototipoV2/02_modelo_prototipo/modelo_mitigado",
}

CONJUNTOS = {
    "test":  (RAIZ / "data/dataset_b2/test.csv",             "texto_modelo"),
    "adv":   (RAIZ / "data/dataset_b2/test_adversarial.csv", "texto_normalizado"),
    "val":   (RAIZ / "data/dataset_b2/val.csv",              "texto_modelo"),
}

MAX_LEN = 128


def sha256(p, tope=None):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def cargar(nombre):
    d = MODELOS[nombre]
    # xlmr_v1 no trae tokenizer.json propio en algunos casos: usa el de la carpeta
    tok = AutoTokenizer.from_pretrained(str(d))
    mod = AutoModelForSequenceClassification.from_pretrained(str(d))
    mod.eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mod.to(dev)
    return tok, mod, dev


@torch.no_grad()
def logits_de(textos, tok, mod, dev, bs=32):
    out = []
    for i in range(0, len(textos), bs):
        lote = textos[i:i + bs]
        enc = tok(lote, return_tensors="pt", truncation=True,
                  max_length=MAX_LEN, padding=True).to(dev)
        enc.pop("token_type_ids", None) if mod.config.model_type == "xlm-roberta" else None
        out.append(mod(**enc).logits.float().cpu().numpy())
    return np.concatenate(out, 0)


def main():
    torch.manual_seed(42)
    np.random.seed(42)
    manifiesto = {}

    quiere = sys.argv[1:] or list(MODELOS)
    for nombre in quiere:
        ruta = MODELOS[nombre]
        print(f"\n=== {nombre}  ({ruta})", flush=True)
        h = sha256(ruta / "model.safetensors")
        print(f"  sha256 pesos: {h}", flush=True)
        tok, mod, dev = cargar(nombre)
        print(f"  dispositivo: {dev} | arquitectura: {mod.config.architectures}", flush=True)
        manifiesto[nombre] = {"ruta": str(ruta), "sha256": h,
                              "arquitectura": mod.config.architectures,
                              "id2label": mod.config.id2label}

        for cj, (csv, col) in CONJUNTOS.items():
            df = pd.read_csv(csv)
            df.columns = [c.lstrip("﻿") for c in df.columns]
            textos = df[col].astype(str).tolist()
            L = logits_de(textos, tok, mod, dev)
            np.save(SALIDA / f"logits_{nombre}_{cj}.npy", L)
            print(f"  {cj:5s} n={len(textos):5d} -> logits_{nombre}_{cj}.npy", flush=True)

        del mod
        torch.cuda.empty_cache()

    p = SALIDA / "manifiesto_pesos.json"
    prev = json.loads(p.read_text()) if p.exists() else {}
    prev.update(manifiesto)
    p.write_text(json.dumps(prev, indent=2, ensure_ascii=False))
    print("\nlisto")


if __name__ == "__main__":
    main()
