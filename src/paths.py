# -*- coding: utf-8 -*-
"""Rutas del proyecto en un solo lugar. Los scripts vigentes importan de aquí en vez de escribir rutas a mano.

Estructura de data/ (ver data/README.md):
    sources/      lo recolectado (corpus de la Etapa I, X de oct. 2026, hilos de X)
    annotation/   anotación (Etapa I e hilos: blind, labels, predictions, review)
    dataset/      EL dataset vigente (versión DATASET_VERSION)
    history/      versiones anteriores del dataset (v1.0.0 … v1.7.0), solo para reproducir cifras reportadas
    evaluation/   conjuntos que nunca entrenan: frozen_bank (banco congelado) y hard_cases
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
DATASET = DATA / "dataset"
DATASET_VERSION = "1.8.0"
HISTORY = DATA / "history"
SOURCES = DATA / "sources"
X_THREADS = SOURCES / "x_threads"
ANNOTATION = DATA / "annotation"
THREADS = ANNOTATION / "threads"
THREAD_LABELS = THREADS / "labels"
EVALUATION = DATA / "evaluation"
FROZEN_BANK = EVALUATION / "frozen_bank"
HARD_CASES = EVALUATION / "hard_cases"
AFFECTIVE_PROBE = HARD_CASES / "probe_vulgaridad_afectiva_SOLO_EVALUAR.csv"

REPORTS = ROOT / "reports"
REPORTS_IMPROVEMENT = REPORTS / "improvement"
MODELS = ROOT / "models"
RUNS = ROOT / "runs"


def history(version: str) -> Path:
    """Carpeta de una versión anterior del dataset, p. ej. history("1.5.0")."""
    return HISTORY / f"v{version.lstrip('v')}"
