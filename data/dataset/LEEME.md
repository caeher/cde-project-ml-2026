# Dataset v2.0.0 — guía para entrenar y evaluar (6 de noviembre de 2026)

Distribución estándar ≈ 75 / 10 / 15. Todos los modelos del equipo deben entrenarse y evaluarse con **estos mismos archivos** para que las cifras sean comparables.

| Archivo | Filas | % | Uso | NT / OF / OD / AM |
|---|---|---|---|---|
| `train.csv` | 20,028 | 75.2 | **Entrenar** (único archivo que entrena) | 8,914 / 5,453 / 2,876 / 2,785 |
| `val.csv` + `val_hilos.csv` | 459 + 2,314 | 10.4 | **Elegir** (early stopping, checkpoint, umbral, temperatura) | val_hilos: 1,559 / 594 / 29 / 132 |
| `test_hilos.csv` + `../evaluation/frozen_bank/*.csv` | 1,975 + 1,391 | 12.6 | **Reportar** (test principal). Nunca para elegir | test_hilos: 1,307 / 514 / 28 / 126 |
| `test.csv` | 460 | 1.7 | Reportar aparte (test oficial de la Etapa I, continuidad) | 123 / 159 / 95 / 83 |
| `test_adversarial.csv` | 144 | — | Batería de robustez | — |

Clases: 0 No Tóxico · 1 Lenguaje Ofensivo · 2 Discurso de Odio · 3 Amenazas/Violencia (guía: `docs/guia_anotacion.md`).

## Reglas
1. **No agregar datos externos al train sin comprobar fugas** contra val, test, val_hilos, test_hilos y el banco (`python src/data/auditar_dataset.py`). En la v1.x un modelo del equipo tenía 319 de los 460 textos del test dentro de su train.
2. **No usar test_hilos, test ni el banco para elegir nada** (épocas, semilla, hiperparámetros). Eso va con val + val_hilos.
3. **Texto de entrada:** en `train.csv`, `val.csv` y `test.csv` usar la columna `texto_modelo` (ya normalizada). `val_hilos.csv`, `test_hilos.csv` y el banco traen solo `texto_original`: pasarlo por `src/features/normalization.py → normalizar()` (v1.2) antes de tokenizar. Es la misma función que usa la API.
4. **max_length 128**, variante *cased* del modelo base (las *uncased* quitan las tildes).
5. **Reportar** F1-macro con IC bootstrap en el test principal (test_hilos + banco), recall por clase, FPR sobre No Tóxico y, aparte, el test oficial. El evaluador de referencia es `src/evaluation/comparar_v2.py`; si el modelo se guarda como `models/<nombre>/semilla_<s>/modelo` (formato Hugging Face), se evalúa con `python src/evaluation/comparar_v2.py v3.4.0 <nombre>`.

## Cómo se construyó
- `src/data/particion_v2.py` aparta 18 hilos completos de la ronda 3 (3 por tema para val y 3 para test) y el 30 % de las búsquedas de jerga. Regla fijada antes de entrenar, semilla 2026, solo con etiquetas. Resultado en `particion_hilos.json`.
- `src/data/build_dataset_final.py` construye todo y aborta si un texto de evaluación aparece en train (exacto o normalizado).
- Solo textos con consenso A = B en val_hilos y test_hilos. Las etiquetas de los hilos son consenso de anotadores LLM (κ = 0.844), sin validación humana.
- Las columnas `p0…p3` son etiquetas blandas (proporción de votos de los anotadores); se pueden ignorar.
- Detalle y criterios: `docs/improvement/Plan_v2_particion_hilos.md`; historial: `data/history/VERSIONS.md`.
