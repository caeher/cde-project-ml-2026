# src/

Todo se ejecuta desde la raíz del repo con el entorno `.venv` (p. ej. `.venv\Scripts\python.exe src/data/build_dataset_final.py`). Las rutas salen de `paths.py`.

| Carpeta / archivo | Qué hay | Estado |
|---|---|---|
| `paths.py` | Rutas del proyecto y versión vigente del dataset | vigente |
| `data/` | `build_dataset_final.py` (constructor **único** del dataset vigente y del banco congelado), `label_mapping.py`, `lexicon_emojis.py`, `augmentation.py`; constructores de versiones anteriores (`build_dataset_b2.py`, `build_dataset_v4.py`) | vigente / histórico |
| `data/threads/` | scripts de apoyo para preparar y evaluar lotes de hilos | histórico |
| `features/normalization.py` | Normalización v1.2, la misma en entrenamiento e inferencia | vigente |
| `models/inference.py` | `probs_propio` (probabilidades de una carpeta de modelos o ensamble) y `cache` (runs/ext/) | vigente |
| `train/` | `entrenar_v5.py` (receta de entrenamiento), `optuna_cv_hilo.py` (fase 2), `destilar.py` (fase 4); `entrenar_v4.py` | vigente / histórico |
| `evaluation/metrics.py` | `f1m`, `ic_f1`, `ic_delta`, `mcnemar` | vigente |
| `evaluation/` | `banco_externo.py`, `comparar_fase3.py`, `fairness.py`, `prueba_atajos*.py`, `calibracion.py`; comparadores de cada versión (`comparar_v4/v5/v330/v340.py`, `comparar_candidato.py`, `combinar_modelos.py`) | vigente / histórico |
| `v3/` | Etapa II: construcción del dataset v1.2.0, HPO, entrenamiento RoBERTuito, ensemble, figuras y documento | histórico (reproduce la Etapa II) |
| `audit/` | Auditoría 2v de mBERT y XLM-R | histórico |

Compatibilidad: `comparar_v4.py`, `comparar_modelos.py` y `combinar_modelos.py` re-exportan las funciones que se movieron a `evaluation/metrics.py` y `models/inference.py`, así que los imports antiguos siguen funcionando.
