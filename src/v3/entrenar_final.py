# -*- coding: utf-8 -*-
"""
Etapa 3: entrenamiento del modelo final con la configuración ganadora.

Entrena con varias semillas y se queda con la mediana, no con la mejor: elegir
la semilla que más sube sobre validación es una forma silenciosa de sobreajustar
al conjunto de selección, y la tesina tiene que reportar un número que se
sostenga al repetir el experimento.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "reports/v3_arquitectura"
SEMILLAS = [42, 1337, 2026]


def correr(modelo_hf, alias, train, cfg, destino, semilla):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    cmd = [sys.executable, str(RAIZ / "src/v3/entrenar.py"), modelo_hf, alias,
           "--train", str(train), "--salida", str(destino), "--json-salida", str(tmp),
           "--epochs", str(cfg["epochs"]), "--lr", str(cfg["lr"]), "--bs", str(cfg["bs"]),
           "--weight-decay", str(cfg["weight_decay"]), "--warmup", str(cfg["warmup"]),
           "--peso-sintetico", str(cfg["peso_sintetico"]),
           "--fases-reales", str(cfg["fases_reales"])]
    if not cfg.get("pesos_clase", True):
        cmd.append("--sin-pesos-clase")
    env = {"SEMILLA": str(semilla)}
    r = subprocess.run(cmd + ["--semilla", str(semilla)], capture_output=True, text=True)
    if tmp.exists() and tmp.stat().st_size:
        d = json.loads(tmp.read_text()); tmp.unlink(); return d
    tmp.unlink(missing_ok=True)
    print((r.stderr or "")[-400:])
    return None


def main():
    mejor = json.loads((SALIDA / "hpo_robertuito_mejor.json").read_text())
    cfg = mejor["mejores_parametros"]
    modelo_hf = mejor["modelo"]; train = Path(mejor["train"])
    print(f"configuración ganadora (val F1 {mejor['mejor_val_f1']:.4f}):")
    for k, v in cfg.items():
        print(f"  {k:16s} {v}")

    res = []
    for s in SEMILLAS:
        destino = RAIZ / "models/v3" / (f"final_s{s}")
        print(f"\n>>> semilla {s}", flush=True)
        r = correr(modelo_hf, f"final_s{s}", train, cfg, destino, s)
        if r:
            r["semilla"] = s; res.append(r)
            print(f"<<< val F1 = {r['val_f1_macro']:.4f}", flush=True)

    res.sort(key=lambda x: x["val_f1_macro"])
    mediana = res[len(res) // 2]
    (SALIDA / "final_semillas.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    import shutil
    destino = RAIZ / "models/v3/final"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(RAIZ / "models/v3" / f"final_s{mediana['semilla']}", destino)

    print(f"\n{'='*60}")
    for r in res:
        marca = "  <- mediana, elegido" if r["semilla"] == mediana["semilla"] else ""
        print(f"  semilla {r['semilla']:5d}  val F1 = {r['val_f1_macro']:.4f}{marca}")
    print(f"\nmodelo final -> {destino}")


if __name__ == "__main__":
    main()
