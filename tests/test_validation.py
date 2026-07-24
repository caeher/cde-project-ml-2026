"""Pruebas del protocolo de validación."""

from __future__ import annotations

import pandas as pd

from discurso_odio.data.agreement import extract_kappa_from_dataset
from discurso_odio.data.validation import apply_validation_protocol


def test_validation_protocol_populates_fields():
    df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4],
            "Responsable": ["Cristian", "Willian", "Dressler", "Cristian"],
            "Clase_Toxicidad": ["No Tóxico", "Discurso de odio", "Amenazas/Violencia", "Lenguaje Ofensivo"],
            "Confianza_Clasificador": [0.9, 0.7, 0.85, 0.6],
            "Validado": ["No", "No", "No", "No"],
            "Validador": [None, None, None, None],
            "Acuerdo_Validador": [None, None, None, None],
            "Cohen_Kappa": [None, None, None, None],
        }
    )
    validated = apply_validation_protocol(df, seed=42)
    assert validated["Validador"].notna().any()
    report = extract_kappa_from_dataset(validated)
    assert report["validated_count"] >= 1
