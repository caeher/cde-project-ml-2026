# -*- coding: utf-8 -*-
"""Etapa 1: comparación de arquitecturas con hiperparámetros idénticos."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.v3.entrenar import entrenar, RAIZ

SALIDA = RAIZ / "reports/v3_arquitectura"

CANDIDATOS = [
    # alias,            modelo_hf,                                      bs, acum
    ("xlmr_base",       "xlm-roberta-base",                              16, 1),
    ("twitter_xlmr",    "cardiffnlp/twitter-xlm-roberta-base",           16, 1),
    ("robertuito",      "pysentimiento/robertuito-base-cased",           16, 1),
    ("bertin",          "bertin-project/bertin-roberta-base-spanish",    16, 1),
    ("beto",            "dccuchile/bert-base-spanish-wwm-cased",         16, 1),
    ("mbert",           "bert-base-multilingual-cased",                  16, 1),
    ("xlmr_large",      "xlm-roberta-large",                              8, 2),
]

def main():
    p = SALIDA / "bakeoff.json"
    res = json.loads(p.read_text()) if p.exists() else []
    hechos = {r["alias"] for r in res}
    for alias, hf, bs, acum in CANDIDATOS:
        if alias in hechos:
            print(f"[salto] {alias} ya hecho", flush=True); continue
        print(f"\n{'='*70}\n>>> {alias}  ({hf})\n{'='*70}", flush=True)
        try:
            r = entrenar(hf, alias, RAIZ / "data/dataset_b2/train.csv",
                         RAIZ / "models/v3" / alias, epochs=4, lr=2e-5, bs=bs, acum=acum)
            print(f"<<< {alias}: val F1-macro = {r['val_f1_macro']:.4f}  ({r['minutos']} min)", flush=True)
        except Exception as e:
            traceback.print_exc()
            r = dict(alias=alias, modelo_hf=hf, error=str(e)[:300])
            print(f"<<< {alias}: FALLÓ", flush=True)
        res.append(r); p.write_text(json.dumps(res, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}\nRESUMEN DEL BAKE-OFF (val, n=459)\n{'='*70}")
    ok = [r for r in res if "val_f1_macro" in r]
    for r in sorted(ok, key=lambda x: -x["val_f1_macro"]):
        print(f"  {r['alias']:16s} F1={r['val_f1_macro']:.4f}  acc={r['val_accuracy']:.4f}  "
              f"{r['params']/1e6:6.0f}M par.  {r['minutos']:5.1f} min")
    for r in res:
        if "error" in r: print(f"  {r['alias']:16s} FALLÓ: {r['error'][:80]}")

if __name__ == "__main__":
    main()
