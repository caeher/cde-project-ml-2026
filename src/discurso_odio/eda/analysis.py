"""Análisis exploratorio de datos (EDA) del corpus."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from discurso_odio.data.loader import CANONICAL_LABEL_COLUMN, TEXT_COLUMN, prepare_dataset
from discurso_odio.data.taxonomy import CANONICAL_LABELS
from discurso_odio.features.preprocessing import preprocess_dataframe
from discurso_odio.utils.paths import get_project_root

FIGURE_DPI = 120
PALETTE = "Set2"


def _figures_dir() -> Path:
    path = get_project_root() / "reports" / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_fig(name: str) -> Path:
    output = _figures_dir() / name
    plt.tight_layout()
    plt.savefig(output, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()
    return output


def plot_label_distribution(df: pd.DataFrame) -> Path:
    """Distribución de clases canónicas."""
    prepared = prepare_dataset(df)
    counts = prepared[CANONICAL_LABEL_COLUMN].value_counts().reindex(CANONICAL_LABELS, fill_value=0)
    plt.figure(figsize=(8, 5))
    sns.barplot(x=counts.index, y=counts.values, palette=PALETTE)
    plt.title("Distribución de clases de toxicidad")
    plt.xlabel("Clase")
    plt.ylabel("Frecuencia")
    plt.xticks(rotation=20)
    return _save_fig("01_distribucion_clases.png")


def plot_platform_distribution(df: pd.DataFrame) -> Path:
    """Distribución por plataforma (X vs Facebook)."""
    if "Plataforma" not in df.columns:
        return _figures_dir() / "02_plataformas.png"
    prepared = prepare_dataset(df)
    plt.figure(figsize=(6, 4))
    sns.countplot(data=prepared, x="Plataforma", palette=PALETTE)
    plt.title("Publicaciones por plataforma")
    return _save_fig("02_plataformas.png")


def plot_text_length_by_class(df: pd.DataFrame) -> Path:
    """Longitud de texto por clase."""
    prepared = preprocess_dataframe(prepare_dataset(df), TEXT_COLUMN)
    prepared["char_len"] = prepared["texto_limpio"].str.len()
    plt.figure(figsize=(9, 5))
    sns.boxplot(
        data=prepared,
        x=CANONICAL_LABEL_COLUMN,
        y="char_len",
        order=CANONICAL_LABELS,
        palette=PALETTE,
    )
    plt.title("Longitud de texto por clase")
    plt.xlabel("Clase")
    plt.ylabel("Caracteres")
    return _save_fig("03_longitud_por_clase.png")


def plot_dialect_distribution(df: pd.DataFrame) -> Path:
    """Distribución de lenguaje dialectal."""
    if "Lenguaje_Dialectal" not in df.columns:
        return _figures_dir() / "04_dialecto.png"
    prepared = prepare_dataset(df)
    plt.figure(figsize=(8, 4))
    dialect_counts = prepared["Lenguaje_Dialectal"].value_counts().head(8)
    sns.barplot(x=dialect_counts.index, y=dialect_counts.values, palette=PALETTE)
    plt.title("Distribución de lenguaje dialectal")
    plt.xticks(rotation=30)
    return _save_fig("04_dialecto.png")


def plot_cooccurrence_flags(df: pd.DataFrame) -> Path:
    """Co-ocurrencia de sarcasmo, ironía y contexto político."""
    prepared = prepare_dataset(df)
    flags = []
    for col, name in [
        ("Presencia_Sarcasmo", "Sarcasmo"),
        ("Presencia_Ironia", "Ironía"),
        ("Contexto_Politico", "Contexto político"),
    ]:
        if col in prepared.columns:
            yes = prepared[col].astype(str).str.lower().isin({"si", "sí", "s", "yes"}).sum()
            flags.append({"flag": name, "count": yes})
    if not flags:
        return _figures_dir() / "05_flags.png"
    flag_df = pd.DataFrame(flags)
    plt.figure(figsize=(6, 4))
    sns.barplot(data=flag_df, x="flag", y="count", palette=PALETTE)
    plt.title("Presencia de marcadores contextuales")
    return _save_fig("05_flags.png")


def run_full_eda(df: pd.DataFrame) -> list[Path]:
    """Ejecuta el EDA completo y guarda todas las figuras."""
    figures = [
        plot_label_distribution(df),
        plot_platform_distribution(df),
        plot_text_length_by_class(df),
        plot_dialect_distribution(df),
        plot_cooccurrence_flags(df),
    ]
    return figures
