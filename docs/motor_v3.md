# Motor V3 (`modeling_v3`)

Pipeline reproducible de datos congelados, entrenamiento, HPO y evaluación con **RoBERTuito** (`pysentimiento/robertuito-base-cased`).

## Datos

- Ruta canónica: `data/processed/v3/`
- Contrato, hashes SHA-256 y referencia de métricas: [`data/processed/v3/CONTRATO.md`](../data/processed/v3/CONTRATO.md)
- Columna de entrada: `texto_modelo` (normalización v1.2 en `modeling_v3.normalization`)
- Cuatro clases (entero `label` 0–3): No Tóxico, Lenguaje Ofensivo, Discurso de Odio, Amenazas/Violencia

## CLI

Desde la raíz del repo, con el entorno instalado (`pip install -e .`):

```powershell
python -m modeling_v3.cli build-data
python -m modeling_v3.cli train --salida models/v3/final
python -m modeling_v3.cli tune --trials 20 --salida models/v3/hpo
python -m modeling_v3.cli evaluate models/v3/final v3_final --salida models/v3/eval
```

`build-data` valida hashes y filas esperadas sin entrenar. Los comandos `train`, `tune` y `evaluate` **requieren GPU CUDA** (`modeling_v3.device.require_cuda`).

Opciones útiles: `--data-dir`, `--semilla`, `--modelo`, `--rapido` (submuestra para pruebas cortas).

## Referencia de evaluación

- `test.csv`: 460 ejemplos
- F1-macro publicado en V3: **0.8499** (tolerancia práctica ±0.01 entre hardware)
- Los pesos entrenados no se versionan (`models/` en `.gitignore`)

## Reconstrucción de `train.csv`

`build-data --reconstruir` necesita `data/raw/lexicon_salvadoreno.csv`, que no está en el repositorio. El `train.csv` congelado ya incluye sintéticos materializados.

## Etapa I archivada

El código anterior (`discurso_odio`) está documentado en [ARCHIVO_ETAPA1.md](ARCHIVO_ETAPA1.md).
