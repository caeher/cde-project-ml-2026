"""Pruebas de taxonomía y carga de datos."""

import pandas as pd
import pytest

from discurso_odio.data.loader import prepare_dataset
from discurso_odio.data.taxonomy import normalize_label


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("No Tóxico", "no_toxico"),
        ("Lenguaje Ofensivo", "ofensivo"),
        ("Discurso de odio", "odio"),
        ("Amenazas/Violencia", "amenazas"),
        ("Insulto", "ofensivo"),
        ("Acoso", "odio"),
    ],
)
def test_normalize_label(raw, expected):
    assert normalize_label(raw) == expected


def test_prepare_dataset_adds_label_column():
    df = pd.DataFrame(
        {
            "Texto_Original": ["Hola mundo", "Eres un idiota"],
            "Clase_Toxicidad": ["No Tóxico", "Lenguaje Ofensivo"],
        }
    )
    result = prepare_dataset(df)
    assert "label" in result.columns
    assert result["label"].tolist() == ["no_toxico", "ofensivo"]
