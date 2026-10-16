# -*- coding: utf-8 -*-
"""Atajos sobre TEXTOS REALES (no plantilla): intercambio de grupo.
Toma textos reales etiquetados (consenso) que mencionan un grupo de nacionalidad y sustituye SOLO ese término por otro grupo.
Si el modelo no usa el nombre del grupo como atajo, la clase predicha no debe cambiar.
También: anular el término (reemplazar por «ellos») para ver cuánto depende de la palabra.
Uso: python src/evaluation/prueba_atajos_reales.py models/v3.1.0 [models/v3.2.0-rc1 ...]"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import app.api.main as M

GRUPOS = {"venezolan": ["venezolanos", "venezolano", "venezolanas", "venezolana"], "veneco": ["venecos", "veneco"],
          "hondure": ["hondureños", "hondureño"], "nic": ["nicaragüenses", "nicas", "nica"], "mexican": ["mexicanos", "mexicano"],
          "haitian": ["haitianos", "haitiano"], "colombian": ["colombianos", "colombiano"], "migrant": ["migrantes", "inmigrantes"]}
ALT = ["haitianos", "hondureños", "nicaragüenses", "colombianos", "chinos", "migrantes", "salvadoreños"]
PAT = re.compile(r"\b(venezolan\w*|venec\w*|hondure\w*|nicaragüens\w*|nicas?|mexican\w*|haitian\w*|colombian\w*|inmigrantes?|migrantes?)\b", re.I)


def cargar():
    H = RAIZ / "data/hilos_reales/etiquetas"; fr = []
    for f, col in [("consenso_1155.csv", "texto_original"), ("consenso_nuevos.csv", "texto"), ("consenso_migrantes.csv", "texto")]:
        d = pd.read_csv(H / f); d = d[d.consenso >= 0]; fr.append(pd.DataFrame({"texto": d[col], "label": d.consenso}))
    d = pd.concat(fr, ignore_index=True); return d[d.texto.str.contains(PAT)].reset_index(drop=True)


def main():
    d = cargar(); print("textos reales con mención de nacionalidad/migrantes:", len(d), "| por clase:", np.bincount(d.label, minlength=4).tolist())
    rng = np.random.default_rng(0)
    swap = [PAT.sub(lambda m: ALT[rng.integers(len(ALT))], t, count=1) for t in d.texto]
    anul = [PAT.sub("ellos", t, count=1) for t in d.texto]
    for ruta in sys.argv[1:]:
        M._modelos.clear(); M.MODELOS = Path(ruta)
        p0 = np.array([M.predecir(t)["label"] for t in d.texto]); p1 = np.array([M.predecir(t)["label"] for t in swap]); p2 = np.array([M.predecir(t)["label"] for t in anul])
        print(f"\n{Path(ruta).name}:  acierto original {(p0==d.label).mean():.3f}")
        print(f"  cambiar el grupo por otro  → predicción igual en {(p0==p1).mean():.3f}  (cambia a más tóxica {(p1>p0).mean():.3f} · a menos tóxica {(p1<p0).mean():.3f})")
        print(f"  anular el término («ellos») → predicción igual en {(p0==p2).mean():.3f}")
        o = d.label.values == 2
        print(f"  solo textos de Odio (n={int(o.sum())}): sigue Odio al cambiar el grupo {(p1[o]==2).mean():.3f} · original {(p0[o]==2).mean():.3f} · sin el término {(p2[o]==2).mean():.3f}")


if __name__ == "__main__":
    main()
