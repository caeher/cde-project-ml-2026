"""Dispositivo de cómputo: el motor V3 exige GPU."""

from __future__ import annotations

import torch


def require_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "El motor V3 requiere una GPU con CUDA. "
            "No se admite entrenar ni ejecutar el modelo en CPU."
        )
    return torch.device("cuda")
