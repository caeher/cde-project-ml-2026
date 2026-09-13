# -*- coding: utf-8 -*-
"""
Validación cruzada estratificada de 5 pliegues sobre la configuración final.

Se hace sobre train + val unidos (6,661 filas), NUNCA sobre test: el test se
reserva como prueba final única, que es lo que exige la rúbrica. Los sintéticos
se asignan al pliegue completo de entrenamiento y nunca aparecen en el de
evaluación, porque evaluar sobre texto de plantilla inflaría la métrica.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedKFold

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "reports/v3_arquitectura"
N_PLIEGUES = 5


def leer(p):
    d = pd.read_csv(p); d.columns = [c.lstrip("﻿") for c in d.columns]; return d


def main():
    cfg = json.loads((SALIDA / "hpo_robertuito_mejor.json").read_text())
    par, modelo_hf = cfg["mejores_parametros"], cfg["modelo"]

    tr = leer(RAIZ / "data/dataset_v3/train.csv")
    va = leer(RAIZ / "data/dataset_v3/val.csv")
    va["origen"] = "real"
    for c in tr.columns:
        if c not in va.columns:
            va[c] = "" if tr[c].dtype == object else 0
    todo = pd.concat([tr, va[tr.columns]], ignore_index=True)

    reales = todo[todo.origen.astype(str) == "real"].reset_index(drop=True)
    sinteticos = todo[todo.origen.astype(str) != "real"].reset_index(drop=True)
    print(f"reales {len(reales)} · sintéticos {len(sinteticos)} · total {len(todo)}")

    skf = StratifiedKFold(n_splits=N_PLIEGUES, shuffle=True, random_state=42)
    tmpdir = Path(tempfile.mkdtemp())
    res = []
    for k, (i_tr, i_ev) in enumerate(skf.split(reales, reales.label), 1):
        # los sintéticos solo entrenan; se evalúa exclusivamente sobre texto real
        ent = pd.concat([reales.iloc[i_tr], sinteticos], ignore_index=True)
        ev = reales.iloc[i_ev].reset_index(drop=True)
        f_tr, f_ev = tmpdir / f"tr{k}.csv", tmpdir / f"ev{k}.csv"
        ent.to_csv(f_tr, index=False, encoding="utf-8-sig")
        ev.to_csv(f_ev, index=False, encoding="utf-8-sig")

        out = tmpdir / f"r{k}.json"
        cmd = [sys.executable, str(RAIZ / "src/v3/entrenar.py"), modelo_hf, f"cv{k}",
               "--train", str(f_tr), "--val", str(f_ev), "--no-guardar",
               "--salida", str(tmpdir / f"m{k}"), "--json-salida", str(out),
               "--epochs", str(par["epochs"]), "--lr", str(par["lr"]),
               "--bs", str(par["bs"]), "--weight-decay", str(par["weight_decay"]),
               "--warmup", str(par["warmup"]),
               "--peso-sintetico", str(par["peso_sintetico"]),
               "--fases-reales", str(par["fases_reales"]), "--semilla", "42"]
        if not par["pesos_clase"]:
            cmd.append("--sin-pesos-clase")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if out.exists() and out.stat().st_size:
            d = json.loads(out.read_text())
            d["pliegue"] = k; d["n_eval"] = len(ev); res.append(d)
            print(f"  pliegue {k}/{N_PLIEGUES}: F1-macro = {d['val_f1_macro']:.4f}  "
                  f"(entrena {len(ent)}, evalúa {len(ev)} reales)", flush=True)
        else:
            print(f"  pliegue {k}: FALLÓ · {(r.stderr or '')[-200:]}", flush=True)

    f1 = np.array([r["val_f1_macro"] for r in res])
    resumen = {"n_pliegues": len(res), "media": float(f1.mean()), "desv": float(f1.std(ddof=1)),
               "min": float(f1.min()), "max": float(f1.max()),
               "por_pliegue": [{"pliegue": r["pliegue"], "f1_macro": r["val_f1_macro"],
                                "n_eval": r["n_eval"]} for r in res]}
    (SALIDA / "validacion_cruzada.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"\nF1-macro CV {len(res)} pliegues: {f1.mean():.4f} ± {f1.std(ddof=1):.4f}"
          f"   [{f1.min():.4f}, {f1.max():.4f}]")


if __name__ == "__main__":
    main()
