# -*- coding: utf-8 -*-
"""
Motor de inferencia reanudable.

Ordena por longitud para minimizar padding (el cuello de botella en NumPy) y
guarda avance en un .npy para poder continuar entre llamadas.
"""
import os, sys, time, json
import numpy as np

sys.path.insert(0, "/sessions/bold-practical-shannon/mnt/outputs")
from xlmr_numpy import XLMRNumpy, CLASES


def inferir(textos, cache, minutos=0.6, batch_tokens=2048):
    """Devuelve (logits, completo). Reanuda desde `cache` si existe."""
    n = len(textos)
    if os.path.exists(cache):
        L = np.load(cache)
    else:
        L = np.full((n, 4), np.nan, dtype=np.float32)

    m = XLMRNumpy()
    # Longitud real de cada texto para agrupar
    largos = np.array([len(m.tok.encode(t).ids[:128]) for t in textos])
    pendientes = [i for i in range(n) if np.isnan(L[i, 0])]
    pendientes.sort(key=lambda i: largos[i])

    t0, hechos = time.time(), 0
    i = 0
    while i < len(pendientes):
        # Batch dinámico: tantas filas como quepan en batch_tokens
        Lmax = largos[pendientes[i]]
        bs = max(1, min(64, batch_tokens // max(Lmax, 1)))
        idx = pendientes[i:i + bs]
        Lmax = int(largos[idx].max())
        X, M = m.codificar([textos[j] for j in idx], max_length=128)
        L[idx] = m.forward(X, M)
        hechos += len(idx)
        i += bs
        if time.time() - t0 > minutos * 60:
            break

    np.save(cache, L)
    faltan = int(np.isnan(L[:, 0]).sum())
    print(f"  procesados {hechos} | faltan {faltan} | {time.time()-t0:.0f}s", flush=True)
    return L, faltan == 0


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


if __name__ == "__main__":
    import pandas as pd
    from xlmr_numpy import BASE
    df = pd.read_csv(BASE / "01_dataset_y_entrenamiento/data/test.csv")
    L, ok = inferir(df["texto_modelo"].astype(str).tolist(),
                    "/sessions/bold-practical-shannon/mnt/outputs/logits_test.npy",
                    minutos=float(sys.argv[1]) if len(sys.argv) > 1 else 0.6)
    if ok:
        df["y_pred"] = L.argmax(-1)
        P = softmax(L)
        for j, c in enumerate(CLASES):
            df[f"p{j}"] = P[:, j]
        df.to_csv("/sessions/bold-practical-shannon/mnt/outputs/preds_test.csv",
                  index=False, encoding="utf-8-sig")
        print("COMPLETO -> preds_test.csv")
