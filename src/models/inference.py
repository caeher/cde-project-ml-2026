# -*- coding: utf-8 -*-
"""Inferencia con los modelos propios (carpetas de models/) y caché de probabilidades en runs/ext/.

Antes vivía en src/evaluation/combinar_modelos.py, que la sigue re-exportando. La carga reutiliza la de la API
(app/api/main.py: manifest de ensamble, varias semillas), así que las probabilidades son las mismas que sirve la API.
"""
import re
from pathlib import Path
import numpy as np, torch
from src import paths as P

CACHE = P.RUNS / "ext"; CACHE.mkdir(exist_ok=True, parents=True)


@torch.no_grad()
def probs_propio(ruta, textos):
    from src.features.normalization import normalizar
    import app.api.main as M
    M._modelos.clear(); M.MODELOS = Path(ruta); M._cargar()
    tx = [normalizar(str(t)) for t in textos]; orden = np.argsort([len(t) for t in tx]); out = np.zeros((len(tx), 4))  # por lotes y ordenado por longitud: mismo resultado, mucho más rápido
    for i in range(0, len(tx), 64):
        idx = orden[i:i + 64]; enc = M._tok([tx[j] for j in idx], truncation=True, max_length=128, padding=True, return_tensors="pt").to(M._dev)
        out[idx] = np.mean([torch.softmax(m(**enc).logits.double(), -1).cpu().numpy() for m in M._modelos], 0)
    return out


def cache(nombre, fn):
    f = CACHE / (re.sub(r"[^\w.-]", "_", nombre) + ".npy")
    if f.exists(): return np.load(f)
    a = fn(); np.save(f, a); return a
