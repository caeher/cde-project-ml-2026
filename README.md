# Análisis del Discurso de Odio en Redes Sociales en El Salvador

Proyecto de Machine Learning para detectar y clasificar discurso de odio en contenido de redes sociales del contexto salvadoreño (UES — ESI 2026).

El desarrollo activo en `main` se centra en el **motor V3** (`src/modeling_v3/`): datos congelados, fine-tuning con RoBERTuito, HPO y evaluación reproducible.

> **Etapa I** (`discurso_odio`, baselines, notebooks 00–04): archivada. Ver [docs/ARCHIVO_ETAPA1.md](docs/ARCHIVO_ETAPA1.md). La rama Git **`v3`** conserva el proyecto completo histórico (app, informes, `src/v3/`) sin modificaciones desde esta consolidación.

## Estructura del proyecto

```
├── config/
│   └── v3.yaml            # Parámetros de referencia V3
├── data/
│   └── processed/v3/      # Splits congelados + CONTRATO.md
├── docs/
│   ├── motor_v3.md        # Uso del motor
│   └── ARCHIVO_ETAPA1.md  # Cómo recuperar Etapa I
├── models/v3/             # Salida local (no versionada)
├── scripts/
│   └── verify_hf_env.py   # Verificación HF / CUDA (TFM-21)
├── src/
│   └── modeling_v3/       # Motor V3: datos, train, HPO, evaluación
└── tests/
    └── test_modeling_v3.py
```

## Requisitos

- Python 3.10 o superior
- pip
- GPU con **CUDA** para entrenar y evaluar modelos (no para `build-data` ni tests unitarios)

## Configuración del entorno

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Sesión Hugging Face (`hf auth whoami`) para descargar el modelo base.

Verificación del entorno (sin entrenar el modelo V3 completo):

```powershell
python scripts/verify_hf_env.py
```

## Motor V3 (fine-tuning RoBERTuito)

Splits en `data/processed/v3/` ([contrato y SHA-256](data/processed/v3/CONTRATO.md)). Referencia: **F1-macro 0.8499** en `test.csv` (n=460); tolerancia práctica **±0.01** si el hardware no reproduce el mismo determinismo.

```powershell
python -m modeling_v3.cli build-data
python -m modeling_v3.cli train --salida models/v3/final
python -m modeling_v3.cli tune --trials 20 --salida models/v3/hpo
python -m modeling_v3.cli evaluate models/v3/final v3_final --salida models/v3/eval
```

`train`, `tune` y `evaluate` requieren CUDA. Los pesos no se versionan (`models/` ignorado).

Documentación detallada: [docs/motor_v3.md](docs/motor_v3.md).

## Taxonomía de clases (V3)

| Clase | Índice |
|-------|--------|
| No Tóxico | 0 |
| Lenguaje Ofensivo | 1 |
| Discurso de Odio | 2 |
| Amenazas/Violencia | 3 |

## Documentación

- [Motor V3](docs/motor_v3.md)
- [Archivo Etapa I](docs/ARCHIVO_ETAPA1.md)
- [Plan de migración V3 → main](PLAN_MIGRACION_V3_A_MAIN.md)
- [Reporte de alineación ramas](REPORTE.md)

## Licencia

MIT — ver [LICENSE](LICENSE).
