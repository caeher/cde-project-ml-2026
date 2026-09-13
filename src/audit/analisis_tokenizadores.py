# -*- coding: utf-8 -*-
"""
Análisis de arquitectura, fase 1: adecuación del tokenizador al dialecto.

La hipótesis a contrastar es que buena parte de la brecha entre mBERT y XLM-R
sobre este corpus no viene del transformer sino del vocabulario: cuántos
subtokens gasta cada modelo en una palabra salvadoreña, cuántos [UNK] produce y
cuánto de la jerga del léxico del proyecto sobrevive como token entero.
"""
import json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from transformers import AutoTokenizer
warnings.filterwarnings("ignore")

RAIZ = Path("/home/willian/ues/esp/proyecto"); S = RAIZ / "reports/v3_arquitectura"
S.mkdir(parents=True, exist_ok=True)

CANDIDATOS = {
    "mBERT":            "bert-base-multilingual-cased",
    "XLM-R base":       "xlm-roberta-base",
    "XLM-R large":      "xlm-roberta-large",
    "BETO":             "dccuchile/bert-base-spanish-wwm-cased",
    "RoBERTa-BNE":      "PlanTL-GOB-ES/roberta-base-bne",
    "BERTIN":           "bertin-project/bertin-roberta-base-spanish",
    "RoBERTuito":       "pysentimiento/robertuito-base-cased",
    "TwitterXLM-R":     "cardiffnlp/twitter-xlm-roberta-base",
    "mDeBERTa-v3":      "microsoft/mdeberta-v3-base",
}

def leer(p):
    d = pd.read_csv(RAIZ / p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d

corpus = leer("data/dataset_b2/train.csv")
textos = corpus[corpus.origen == "real"]["texto_modelo"].astype(str).tolist()
lex = leer("data/raw/lexicon_salvadoreno.csv")
col_jerga = "Texto_Original"
jerga = sorted({str(w).strip().lower() for w in lex[col_jerga] if isinstance(w, str) and 2 < len(str(w)) < 20 and " " not in str(w)})
print(f"corpus real: {len(textos)} textos · léxico salvadoreño: {len(jerga)} entradas ({col_jerga})\n")

# palabras que importan: jerga + ofuscaciones típicas
OFUSC = ["p*ta", "put@", "p#ta", "pu74", "pvta", "m4t4r", "m13rda", "v3rg4",
         "hij0s", "d3", "m*tar", "puuuta", "HDP", "cerote", "maje", "chero",
         "pisto", "bicho", "cipote", "chunche", "puchica", "chivo", "bolado"]

filas = []
for nombre, mid in CANDIDATOS.items():
    try:
        tok = AutoTokenizer.from_pretrained(mid)
    except Exception as e:
        print(f"{nombre:14s} NO DISPONIBLE: {str(e)[:70]}"); continue

    enc = tok(textos, add_special_tokens=False)["input_ids"]
    n_sub = np.array([len(e) for e in enc])
    n_pal = np.array([len(t.split()) for t in textos])
    fert = n_sub / np.maximum(n_pal, 1)

    unk = tok.unk_token_id
    n_unk = sum(e.count(unk) for e in enc) if unk is not None else 0

    # jerga: ¿cuántas entradas del léxico son un solo token?
    entero = sum(1 for w in jerga if len(tok.tokenize(w)) == 1)
    frag = np.mean([len(tok.tokenize(w)) for w in jerga])
    frag_of = np.mean([len(tok.tokenize(w)) for w in OFUSC])

    # cobertura a 128 tokens
    trunc = float((n_sub + 2 > 128).mean())

    filas.append(dict(modelo=nombre, hf=mid, vocab=len(tok),
                      fertilidad=float(fert.mean()), p95_subtokens=float(np.percentile(n_sub, 95)),
                      trunc_128=trunc, unk_total=int(n_unk),
                      jerga_1token=entero, jerga_pct=100*entero/len(jerga),
                      frag_jerga=float(frag), frag_ofuscacion=float(frag_of)))
    print(f"{nombre:14s} vocab={len(tok):>7,d}  fert={fert.mean():.3f}  p95={np.percentile(n_sub,95):5.0f}  "
          f"trunc128={trunc*100:4.1f}%  UNK={n_unk:>4d}  jerga1tok={entero:>4d}/{len(jerga)} ({100*entero/len(jerga):4.1f}%)  "
          f"frag_ofusc={frag_of:.2f}")

df = pd.DataFrame(filas).sort_values("fertilidad")
df.to_csv(S / "tokenizadores.csv", index=False, encoding="utf-8-sig")
print(f"\n-> {S/'tokenizadores.csv'}")

# ejemplo cualitativo
print("\n=== segmentación de casos difíciles ===")
muestra = ["Sos un cerote pero te quiero maje", "Te voy a m4t4r", "Qué p*ta madre",
           "Prestame pisto vos", ":pistola_de_agua:"]
for nombre, mid in list(CANDIDATOS.items()):
    try: tok = AutoTokenizer.from_pretrained(mid)
    except Exception: continue
    print(f"\n{nombre}")
    for t in muestra:
        print(f"   {t:36s} -> {tok.tokenize(t)}")
