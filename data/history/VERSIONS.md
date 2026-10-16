# Versiones del dataset

Hay **un solo dataset**; estas carpetas son fotos suyas en el tiempo. Se guardan para reproducir las cifras ya reportadas (Etapa II y `CHANGELOG.md`), **no para entrenar**. El vigente está en `data/dataset/`.

Numeración `dataset vMAJOR.MINOR.PATCH` (distinta de la del modelo, `v3.x.x`):
- **MAJOR:** cambian las clases, la guía de anotación de forma incompatible o la partición val/test.
- **MINOR:** se agregan (o quitan) datos de entrenamiento.
- **PATCH:** correcciones sin datos nuevos (normalización, fugas, duplicados).

Val (459) y test (460) son **los mismos en todas las versiones** (mismos ID, texto, `texto_modelo` y etiqueta): todo es MAJOR 1.

| Versión | Carpeta (antes) | Train | Cambio | Script | Modelo que entrenó |
|---|---|---|---|---|---|
| v1.0.0 | `v1.0.0/` (`data/processed`) | 2,144 | Corpus limpio de la Etapa I (privado) | notebooks 01–02 | baselines Etapa I |
| v1.1.0 | `v1.1.0/` (`dataset_b2`) | 3,293 | Dataset de la Etapa II | `src/data/build_dataset_b2.py` | mBERT / XLM-R (auditoría 2v) |
| v1.2.0 | `v1.2.0/` (`dataset_v3`) | 6,416 | + sintéticos | `src/v3/construir_dataset.py` | RoBERTuito Etapa II |
| v1.3.0 | `v1.3.0/` (`archivo/…v4_normalizacion_v1.1`) | 7,344 | Base b2 + textos de X (oct.), normalización v1.1 (reemplazada por v1.3.1) | `archivo/…/build_dataset_v4_original.py` | — |
| v1.3.1 | `v1.3.1/` (`dataset_v4`) | 10,469 | PATCH: normalización v1.2 y fugas | `src/data/build_dataset_v4.py` | v3.0.0 (textos de oct. con peso 0) |
| v1.4.0-a | `v1.4.0-a/` (`dataset_v5a`) | 6,749 | Experimento con hilos reservados | `archivo/scripts_build/build_dataset_v5.py` | ninguno desplegado |
| v1.4.0 | `v1.4.0/` (`dataset_v5f`) | 7,199 | + 4 hilos reales + casos difíciles; sin X oct. | `archivo/scripts_build/build_dataset_v5.py` | v3.1.0 |
| v1.5.0 | `v1.5.0/` (`dataset_v6`) | 8,164 | Consenso de 3 anotadores, 9 hilos | `archivo/scripts_build/build_dataset_v6.py` | v3.2.0-rc1 |
| v1.6.0 | `v1.6.0/` (`dataset_v7`) | 8,551 | + hilos con Amenazas | `archivo/scripts_build/build_dataset_v7.py` | v3.3.0-rc1 |
| v1.7.0 | `v1.7.0/` (`archivo/datasets/dataset_v8`) | 9,195 | + hilos de Odio (LGBT, racismo) | `archivo/scripts_build/build_dataset_v8.py` | v3.4.0-rc1 (descartado) |
| **v1.8.0** | `data/dataset/` (`dataset_final`) | **12,641** | Pool completo de la fase 1; banco congelado excluido | `src/data/build_dataset_final.py` | **v3.4.0 (vigente)** |

Notas:
- `archivo/datasets/dataset_v7_copia` es una copia idéntica de v1.6.0; se conserva donde estaba.
- Varias versiones repiten `val.csv`, `test.csv` y `test_adversarial.csv` (mismo contenido); se dejan para que cada carpeta sea autocontenida.

## Cómo publicar una versión nueva
1. Cambiar `DATASET_VERSION` en `src/paths.py` y regenerar con `python src/data/build_dataset_final.py`.
2. Copiar la versión anterior a `history/vX.Y.Z/` y agregar su fila aquí.
3. Etiqueta git: `git tag dataset-vX.Y.Z`.
4. El modelo entrenado registra `"dataset": "X.Y.Z"` en su `manifest.json`.
