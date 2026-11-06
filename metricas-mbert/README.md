# mBERT — copia mínima para reproducir release **v6**

Este árbol vive **dentro** del proyecto CDE (`cde-project-ml-2026/metricas-mbert`). Incluye solo lo necesario para volver a entrenar **v6** según la receta registrada (ver `versiones/v6/model/training_run.json` en la copia completa del repo o el resumen abajo).

## Requisitos

- Python 3.10+
- GPU recomendada para tiempos razonables (FP16; ver `config/settings.yaml` perfil `gpu`)

## Instalación

```powershell
cd cde-project-ml-2026\metricas-mbert
python -m venv .venv
.\.venv\Scripts\activate
pip install -U pip
pip install -r requirements-dev.txt
pip install -e .
copy .env.example .env
```

Opcional: `python scripts/check_cuda.py` para comprobar PyTorch/CUDA.

## Checkpoint de inicio (v4)

El run v6 cargó pesos **clasificador + tokenizador** desde `versiones/v4/model` (`init_model_dir`). En esta copia mínima solo están los **JSON del tokenizer y config**; faltan los **pesos** (por ejemplo `model.safetensors` o `pytorch_model.bin`), ignorados en `.gitignore` por tamaño.

Copia un checkpoint HF completo de v4 a `versiones/v4/model/` (desde la copia completa de `metricas-mbert` en el monorepo o desde un artefacto publicado compatible con la línea v4).

Sin esos archivos, `train_mbert` no podrá hacer `from_pretrained` sobre `versiones/v4/model`.

## Sincronizar `data/processed` con el dataset CDE

Desde **esta** carpeta, `scripts/sync_cde_dataset.py` usa por defecto el CDE hermano: `..\` → raíz `cde-project-ml-2026` → `data/dataset/`.

```powershell
python scripts/sync_cde_dataset.py
```

Si la ruta del CDE no es el padre directo:

```powershell
python scripts/sync_cde_dataset.py --cde-root "RUTA\cde-project-ml-2026"
```

## Comprobar que la release **v6** resuelve

```powershell
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('src').resolve())); from discurso_odio.data.loaders import release_dir; print(release_dir('v6'))"
```

Debe mostrar el directorio `versiones\v6\dataset`.

## Reproducir entrenamiento v6

Receta alineada con `training_run.json` (5 épocas, semilla 42, init v4, política `b2_full`, sin boost de plataforma, CE, `label_smoothing` 0, `threat_synthetic_effective_n` 90):

```powershell
python scripts/train_mbert.py `
  --release v6 `
  --output-dir versiones/v6/model `
  --init-model-dir versiones/v4/model `
  --epochs 5 `
  --seed 42 `
  --synthetic-policy b2_full `
  --platform-class-boost none `
  --threat-synthetic-effective-n 90 `
  --loss-type ce `
  --label-smoothing 0
```

**Checkpoint de referencia** del run original: **`checkpoint-4050`** (mejor F1 val; 5 épocas completas). La nueva corrida puede guardar otro prefijo de checkpoint según el estado del disco; compare métricas con `versiones/v6/metrics/mbert_training_v6_full_report.json` si la copiaste junto al árbol.

## Más ayuda

Para documentación amplia del proyecto (estructura completa, evaluación, Argilla), usar el árbol `metricas-mbert` en la raíz del monorepo.
