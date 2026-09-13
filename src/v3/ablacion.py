# -*- coding: utf-8 -*-
"""
Etapa 2: ablación de datos, vocabulario y régimen de entrenamiento.

Con la arquitectura y los hiperparámetros fijos, aísla el efecto de cada
decisión para poder atribuir cada punto de F1 a su causa:

  · corpus  : B2 (lo que ya existía) frente a V3 (con los sintéticos nuevos)
  · vocab   : con y sin los 189 tokens de dominio
  · régimen : sintéticos a peso completo, con peso reducido, o en dos fases
              (primero todo, después solo los ejemplos reales)

La primera corrida mostró que los sintéticos a peso completo CUESTAN F1 sobre la
distribución natural. Las variantes de régimen existen para separar «los datos no
sirven» de «los datos no se estaban usando bien».

Cada experimento corre en su PROPIO proceso: en esta GPU, encadenar tres
entrenamientos dentro del mismo intérprete termina en un fallo CUDA por
fragmentación, y un experimento caído no debe arrastrar a los siguientes.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "reports/v3_arquitectura"
B2 = RAIZ / "data/dataset_b2/train.csv"
V3 = RAIZ / "data/dataset_v3/train.csv"

#  alias                  csv  vocab  peso_sintetico  fases_solo_reales
EXPERIMENTOS = [
    ("b2_base",             B2, False, None, 0),
    ("b2_vocab",            B2, True,  None, 0),
    ("v3_peso1.0",          V3, False, None, 0),
    ("v3_peso0.5",          V3, False, 0.5,  0),
    ("v3_peso0.25",         V3, False, 0.25, 0),
    ("v3_dosfases",         V3, False, None, 2),
    ("v3_peso0.5_dosfases", V3, False, 0.5,  2),
    ("v3_vocab_peso0.5",    V3, True,  0.5,  0),
    ("v3_vocab_dosfases",   V3, True,  None, 2),
]


def correr(modelo_hf, base, alias, csv, vocab, peso, fases) -> dict | None:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    cmd = [sys.executable, str(RAIZ / "src/v3/entrenar.py"), modelo_hf, alias,
           "--train", str(csv), "--epochs", "4", "--lr", "2e-5", "--bs", "16",
           "--salida", str(RAIZ / "models/v3" / f"{base}_{alias}"),
           "--json-salida", str(tmp)]
    if vocab:
        cmd.append("--vocab")
    if peso is not None:
        cmd += ["--peso-sintetico", str(peso)]
    if fases:
        cmd += ["--fases-reales", str(fases)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if tmp.exists() and tmp.stat().st_size:
        d = json.loads(tmp.read_text()); tmp.unlink(); return d
    cola = [l for l in r.stderr.strip().split("\n") if l.strip()][-1:] or ["sin detalle"]
    print(f"    error: {cola[0][:140]}", flush=True)
    tmp.unlink(missing_ok=True)
    return None


def main(modelo_hf: str, base: str):
    p = SALIDA / f"ablacion_{base}.json"
    res = [r for r in (json.loads(p.read_text()) if p.exists() else [])
           if "val_f1_macro" in r]
    hechos = {r["alias"] for r in res}

    for alias, csv, vocab, peso, fases in EXPERIMENTOS:
        if alias in hechos:
            print(f"[salto] {alias}", flush=True); continue
        print(f">>> {base} · {alias}", flush=True)
        r = correr(modelo_hf, base, alias, csv, vocab, peso, fases)
        if r:
            r["variante"] = dict(vocab=vocab, peso_sintetico=peso, fases_reales=fases)
            print(f"<<< {alias}: val F1 = {r['val_f1_macro']:.4f}  ({r['minutos']} min)", flush=True)
            res.append(r)
        else:
            print(f"<<< {alias}: FALLÓ", flush=True)
        p.write_text(json.dumps(res, indent=2, ensure_ascii=False))

    print(f"\n{'='*74}\nABLACIÓN · {base}   (F1-macro sobre val, n=459)\n{'='*74}")
    print(f"  {'variante':22s} {'F1':>7s} {'n_train':>8s} {'tokens':>7s} {'p_sint':>7s} {'fases':>6s}")
    for r in sorted(res, key=lambda x: -x["val_f1_macro"]):
        v = r.get("variante", {})
        print(f"  {r['alias']:22s} {r['val_f1_macro']:7.4f} {r['n_train']:8d} "
              f"{r['tokens_anadidos']:7d} {str(v.get('peso_sintetico')):>7s} "
              f"{v.get('fases_reales', 0):6d}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
