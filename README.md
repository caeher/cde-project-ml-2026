# Análisis del Discurso de Odio en Redes Sociales en El Salvador

Proyecto de Machine Learning para detectar, clasificar y analizar discurso de odio en contenido de redes sociales del contexto salvadoreño (UES — ESI 2026).

## Estructura del proyecto

```
├── config/              # Configuración (YAML)
├── data/
│   ├── raw/             # Datasets recolectados (CSV)
│   ├── interim/         # Datos en transformación intermedia
│   ├── processed/       # Datasets listos para modelado
│   └── external/        # Fuentes externas
├── docs/                # Documentación del proyecto
├── models/
│   └── checkpoints/     # Modelos entrenados
├── notebooks/           # Jupyter notebooks de exploración
├── reports/
│   ├── figures/         # Gráficos EDA y evaluación
│   └── latex/           # Reporte LaTeX (no versionado)
├── scripts/             # Scripts ejecutables (CLI)
├── src/
│   └── discurso_odio/   # Código fuente del paquete
│       ├── data/        # Carga, taxonomía, acuerdo Kappa
│       ├── eda/         # Análisis exploratorio
│       ├── features/    # Preprocesamiento y features
│       ├── models/      # Baselines, evaluación, fine-tuning, interpretabilidad
│       └── utils/       # Utilidades (rutas, helpers)
└── tests/               # Pruebas unitarias
```

## Requisitos

- Python 3.10 o superior
- pip

## Configuración del entorno

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Sesión Hugging Face (`hf auth whoami`) para descarga de modelos base.

Verificación reproducible del entorno (TFM-21):

```bash
python scripts/verify_hf_env.py
```

### Google Colab GPU

Abrir `notebooks/00_colab_setup.ipynb` en Colab con runtime **T4 GPU**. El notebook clona el repo, instala dependencias, autentica Hugging Face y ejecuta la verificación + smoke test de fine-tuning. Ver [docs/etapa1.md](docs/etapa1.md#entorno-reproducible-tfm-21).

## Pipeline de ejecución (Etapa I)

```bash
python scripts/run_validation.py   # Validación cruzada + Kappa
python scripts/run_eda.py              # EDA + reporte Kappa
python scripts/run_baselines.py        # 3 baselines + métricas comparativas
python scripts/run_tune.py             # GridSearchCV (TFM-29)
python scripts/run_finetune.py         # Fine-tuning ligero mBERT + XLM-R
python scripts/run_interpretability.py  # SHAP + LIME
pytest
```

## Taxonomía de clases

| Clase | Descripción |
|-------|-------------|
| `no_toxico` | Contenido neutro |
| `ofensivo` | Lenguaje vulgar u ofensivo |
| `odio` | Discurso de odio o acoso |
| `amenazas` | Amenazas o incitación a la violencia |

## Datasets

| Archivo | Registros | Uso |
|---------|-----------|-----|
| `dataset_unificado.csv` | ~2,286 | Corpus completo |
| `dataset_entrenamiento.csv` | ~2,894 | Entrenamiento |
| `dataset_pruebas.csv` | ~352 | Evaluación |

## Cumplimiento Rúbrica Etapa I

| Criterio | Evidencia |
|----------|-----------|
| Calidad y cantidad de datos | `data/raw/*.csv`, `docs/datos.md` |
| EDA completo | `notebooks/01_eda.ipynb`, `reports/figures/` |
| Preprocesamiento y features | `src/discurso_odio/features/` |
| Baselines y métricas (≥3) | `scripts/run_baselines.py`, `reports/metricas_comparativas.csv` |
| Interpretabilidad SHAP/LIME | `scripts/run_interpretability.py` |
| Código reproducible | Repositorio, tests, README, `scripts/verify_hf_env.py`, `notebooks/00_colab_setup.ipynb` |

## Documentación

- [Etapa I — Alcance y pipeline](docs/etapa1.md)
- [Colab GPU + Hugging Face (TFM-21)](notebooks/00_colab_setup.ipynb)
- [Descripción del dataset](docs/datos.md)
- [Reporte LaTeX Etapa I](reports/latex/reporte_etapa1.tex) — compilar con `reports/latex/build_report.ps1`

## Licencia

MIT — ver [LICENSE](LICENSE).
