# -*- coding: utf-8 -*-
"""
Consola interactiva para probar el clasificador.

Carga el modelo una sola vez y se queda esperando texto, así que responde al
instante en vez de pagar la carga en cada llamada. No necesita que la API esté
levantada: habla directamente con el modelo.

    python3 app/pruebas/consola.py                  modo interactivo
    python3 app/pruebas/consola.py "un texto"       un caso y salir
    cat frases.txt | python3 app/pruebas/consola.py -   una frase por línea
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from src.features.normalization import normalizar

MODELO = RAIZ / "models/v3/final"
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]
COLOR = ["\033[32m", "\033[33m", "\033[35m", "\033[31m"]
RESET, TENUE, NEGRITA = "\033[0m", "\033[90m", "\033[1m"


def cargar():
    tok = AutoTokenizer.from_pretrained(str(MODELO))
    mod = AutoModelForSequenceClassification.from_pretrained(str(MODELO)).eval()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return tok, mod.to(dev), dev


@torch.no_grad()
def clasificar(textos, tok, mod, dev):
    norm = [normalizar(t) for t in textos]
    enc = tok(norm, return_tensors="pt", truncation=True, max_length=128,
              padding=True).to(dev)
    log = mod(**enc).logits.float().cpu().numpy()
    p = np.exp(log - log.max(-1, keepdims=True))
    return norm, p / p.sum(-1, keepdims=True)


def barra(v, ancho=22):
    lleno = int(round(v * ancho))
    return "█" * lleno + "·" * (ancho - lleno)


def mostrar(original, norm, probs, detalle=True):
    i = int(probs.argmax())
    print(f"\n  {COLOR[i]}{NEGRITA}{CLASES[i]}{RESET}   {probs[i]:.1%}")
    if not detalle:
        return
    for j, c in enumerate(CLASES):
        marca = COLOR[j] if j == i else TENUE
        print(f"    {marca}{c:20s} {barra(probs[j])} {probs[j]:6.2%}{RESET}")
    if norm != original:
        print(f"    {TENUE}el modelo lee: {norm}{RESET}")


def main():
    args = sys.argv[1:]
    print(f"{TENUE}cargando {MODELO.name}…{RESET}", file=sys.stderr)
    tok, mod, dev = cargar()

    if args and args[0] == "-":
        lineas = [l.strip() for l in sys.stdin if l.strip()]
        norm, probs = clasificar(lineas, tok, mod, dev)
        for t, n, p in zip(lineas, norm, probs):
            print(f"{CLASES[int(p.argmax())]:20s} {p.max():6.1%}  {t}")
        return

    if args:
        norm, probs = clasificar([" ".join(args)], tok, mod, dev)
        mostrar(" ".join(args), norm[0], probs[0])
        return

    print(f"{TENUE}listo en {dev}. Escribí un texto y Enter; Ctrl-D para salir.{RESET}")
    while True:
        try:
            t = input(f"\n{NEGRITA}› {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if not t:
            continue
        if t in ("salir", "exit", "quit"):
            return
        norm, probs = clasificar([t], tok, mod, dev)
        mostrar(t, norm[0], probs[0])


if __name__ == "__main__":
    main()
