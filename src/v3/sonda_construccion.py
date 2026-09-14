# -*- coding: utf-8 -*-
"""
Sonda del atajo sintáctico «te voy a X».

Mide si el modelo aprendió la CONSTRUCCIÓN como señal de amenaza en lugar del
verbo que la completa. Es el mismo tipo de atajo que el del emoji en la v1, y se
detecta igual: pares mínimos donde solo cambia lo que debería decidir la clase.

Un modelo sano debe separar «te voy a matar» de «te voy a llamar». Uno que
aprendió el atajo marca las dos igual.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

# (texto, clase esperada) — el portador es idéntico; cambia solo el verbo
BENIGNOS = [
    "voy a comer", "voy a dormir", "voy a salir", "voy a estudiar",
    "voy a trabajar mañana", "voy a llamar a mi mamá", "voy a comprar pan",
    "te voy a llamar más tarde", "te voy a mandar la foto", "te voy a ver mañana",
    "te voy a extrañar mucho", "te voy a esperar en la parada",
    "te voy a ayudar con la tarea", "te voy a invitar a comer",
    "te voy a prestar el libro", "te voy a contar lo que pasó",
    "te voy a explicar de nuevo", "te voy a acompañar al doctor",
    "lo voy a buscar en internet", "los voy a invitar el domingo",
    "hay que llamarlos a todos", "vamos a comer pupusas",
    "alguien debería ayudarle a ese", "te van a llamar mañana",
]
AMENAZAS = [
    "te voy a matar", "te voy a m4t4r", "te voy a quebrar",
    "te voy a partir la cara", "te voy a dar piso",
    "lo voy a reventar cuando lo vea", "los voy a quemar a todos",
    "hay que matarlos a todos", "alguien debería matar a ese tipo",
    "te van a matar si seguís así",
]


def cargar(ruta):
    tok = AutoTokenizer.from_pretrained(str(ruta))
    mod = AutoModelForSequenceClassification.from_pretrained(str(ruta)).eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return tok, mod.to(dev), dev


@torch.no_grad()
def probabilidades(textos, tok, mod, dev):
    e = tok([normalizar(t) for t in textos], return_tensors="pt",
            truncation=True, max_length=128, padding=True).to(dev)
    L = mod(**e).logits.float().cpu().numpy()
    P = np.exp(L - L.max(-1, keepdims=True))
    return P / P.sum(-1, keepdims=True)


def evaluar(ruta, verbose=True):
    tok, mod, dev = cargar(ruta)
    Pb = probabilidades(BENIGNOS, tok, mod, dev)
    Pa = probabilidades(AMENAZAS, tok, mod, dev)
    del mod
    torch.cuda.empty_cache()

    fp = [(t, p[3]) for t, p in zip(BENIGNOS, Pb) if p.argmax() == 3]
    fn = [(t, p[3]) for t, p in zip(AMENAZAS, Pa) if p.argmax() != 3]
    r = {"falsos_positivos": len(fp), "n_benignos": len(BENIGNOS),
         "amenazas_perdidas": len(fn), "n_amenazas": len(AMENAZAS),
         "p_amenaza_media_benignos": float(Pb[:, 3].mean()),
         "p_amenaza_media_amenazas": float(Pa[:, 3].mean())}
    r["separacion"] = r["p_amenaza_media_amenazas"] - r["p_amenaza_media_benignos"]

    if verbose:
        print(f"  benignos marcados como amenaza : {r['falsos_positivos']:2d}/{r['n_benignos']}")
        print(f"  amenazas no detectadas         : {r['amenazas_perdidas']:2d}/{r['n_amenazas']}")
        print(f"  p(amenaza) media en benignos   : {r['p_amenaza_media_benignos']:.1%}")
        print(f"  p(amenaza) media en amenazas   : {r['p_amenaza_media_amenazas']:.1%}")
        print(f"  separación                     : {r['separacion']:+.1%}")
        if fp:
            print("  falsos positivos:")
            for t, p in sorted(fp, key=lambda x: -x[1]):
                print(f"    {p:5.1%}  {t}")
    return r


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "models/v3/final"
    print(f"=== sonda de construcción sobre {ruta.name} ===")
    evaluar(ruta)
