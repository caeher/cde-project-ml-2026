# Documentación del Proyecto — Etapa I

## Alcance (TFM-18)

Proyecto UES: clasificación multiclase de toxicidad y discurso de odio en publicaciones de X y Facebook del contexto salvadoreño, siguiendo metodología CRISP-DM.

**Objetivo general:** desarrollar un modelo de clasificación automática mediante fine-tuning de mBERT y XLM-R.

**Clases canónicas:**
| Clase | Descripción |
|-------|-------------|
| `no_toxico` | Contenido neutro |
| `ofensivo` | Lenguaje vulgar u ofensivo sin ataque a grupo protegido |
| `odio` | Discurso de odio o acoso dirigido |
| `amenazas` | Amenazas o incitación a la violencia |

## Fuentes de datos (TFM-22)

| Archivo | Registros | Descripción |
|---------|-----------|-------------|
| `data/raw/dataset_unificado.csv` | ~2,286 | Corpus completo recolectado manualmente |
| `data/raw/dataset_entrenamiento.csv` | ~2,894 | Split de entrenamiento |
| `data/raw/dataset_pruebas.csv` | ~352 | Split de prueba |

**Plataformas:** X (Twitter) y Facebook.  
**Recolección:** manual (copiar/pegar de publicaciones públicas), respetando términos de servicio.  
**Anonimización:** IDs de usuario anonimizados (`USER_*`, `USR_*`).

## Guía de etiquetado y Kappa (TFM-20, TFM-24, TFM-25)

- Etiquetado manual por anotadores: Cristian, Dressler, Willian.
- Validación cruzada documentada en columnas `Validado`, `Validador`, `Acuerdo_Validador`.
- Cohen's Kappa calculado en `src/discurso_odio/data/agreement.py`.
- Reporte generado en `reports/kappa_report.json` al ejecutar `scripts/run_eda.py`.

## Entorno reproducible (TFM-21)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Sesión Hugging Face activa (`hf auth whoami`). Modelos base descargados automáticamente al ejecutar fine-tuning.

## Pipeline de ejecución

```bash
python scripts/run_eda.py              # EDA + Kappa
python scripts/run_baselines.py        # 3 baselines + métricas
python scripts/run_tune.py             # GridSearchCV
python scripts/run_finetune.py         # mBERT + XLM-R (ligero)
python scripts/run_interpretability.py  # SHAP + LIME
pytest
```

## Cumplimiento Rúbrica Etapa I

| Criterio | Puntos | Evidencia |
|----------|--------|-----------|
| Calidad y cantidad de datos | 20 | `data/raw/*.csv`, `docs/datos.md` |
| EDA completo | 20 | `notebooks/01_eda.ipynb`, `reports/figures/` |
| Preprocesamiento y features | 20 | `src/discurso_odio/features/`, `notebooks/02_preprocesamiento.ipynb` |
| Baselines y métricas | 20 | `scripts/run_baselines.py`, `reports/metricas_comparativas.csv` |
| Interpretabilidad | 10 | `scripts/run_interpretability.py`, `reports/figures/06_shap_summary.png` |
| Código reproducible | 10 | Repositorio GitHub, tests, README |
