# Entrenamiento XLM-R + HatEval (Julio)

Notebook importado desde `origin/newprotypeV3` (commit `b3f5606`).

- Datos fusionados: [`data/external/hateval/train_merged_hateval.csv`](../../../data/external/hateval/train_merged_hateval.csv)
- Validación / test del proyecto: `data/dataset/val_hilos.csv`, `test_hilos.csv`
- Pesos de salida sugeridos: `models/xlmr_hate_speech_sv/` (gitignored salvo `config.json` si se versiona a mano)

Ejecutar desde la raíz del repo o desde esta carpeta; el notebook resuelve la raíz automáticamente.

## Entrenamiento final integrado

El notebook conserva experimentos anteriores de Colab, subidas al Hub y sus
resultados históricos. Para entrenar con los archivos del repositorio, comenzar
en la celda **«FASE 2: FINE-TUNING DE XLM-ROBERTA-LARGE + HATEVAL FUSIONADO»**
(índice 57, desde cero). Es independiente de las celdas anteriores y lee el CSV
fusionado ya versionado y las particiones `val_hilos`/`test_hilos` vigentes.
No es necesario ejecutar la preparación histórica ni subir archivos manualmente.

El modelo y su tokenizador se guardan en `models/xlmr_hate_speech_sv/`, la
misma ruta utilizada por `xlmr_local` en la API y por los scripts de
`prototype/`. La celda posterior de publicación es opcional y requiere una
cuenta con permisos sobre el repositorio de destino. La optimización posterior
resuelve también val/test desde la raíz y guarda sus artefactos separados en
`runs/modelo_xlmr_large_hateval_optimizado/`.

Requiere las dependencias de `requirements.txt`, acceso al modelo base y
memoria suficiente para entrenar XLM-R large. No usar la configuración de XLM-R
base que se conserva en `prototype/` para el modelo large.
