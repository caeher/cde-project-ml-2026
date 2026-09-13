# Reparto de Tareas — Etapa II

**Actualizado:** 14 de agosto de 2026 · tras la auditoría de modelos y la entrega del dataset B2

---

## Ya está hecho

| Entregable | Estado |
|---|---|
| Dataset B2 (`data/dataset_b2/`) — 3,293 train, val y test intactos | Listo |
| Catálogo de emojis reconstruido — 51 entradas | Listo |
| Conjunto diagnóstico adversarial — 75 casos | Listo |
| Auditoría de ambos modelos (`Informe_Auditoria_de_Modelos.docx`) | Listo |
| Comparativa estadística (`Informe_Comparativa_mBERT_vs_XLMR.docx`) | Listo |
| Script de comparación pareada (`src/evaluation/comparar_modelos.py`) | Listo |
| Predicciones de XLM-R sobre test (`reports/preds_xlmr.csv`) | Listo |

---

## Julio — XLM-RoBERTa

### Correcciones del informe *(bloqueante, antes de reentrenar)*

| # | Tarea | Severidad |
|---|---|---|
| 1 | Recalcular el FPR por jerga. Quitar el `fpr_values = [0.142, 0.385]` escrito a mano en `estadisticas.ipynb`. Los reales son **15.96%** y **44.83%** | Crítica |
| 2 | Corregir `Presencia_Sar` → `Presencia_Sarcasmo` y `Presencia_Iro` → `Presencia_Ironia`, y comparar contra `"SI"`/`"SÍ"`, no contra `1`. Regenerar la Figura 4 | Crítica |
| 3 | Sustituir en §3.1 los valores por plataforma: son **0.867** y **0.715**, no 0.85 y 0.69 (esos son de mBERT) | Crítica |
| 4 | Unificar `max_length = 128` entre entrenamiento e inferencia (el notebook usa 256) | Alta |
| 5 | Añadir al informe intervalo bootstrap, matriz de confusión numérica y métricas con 4 decimales | Alta |
| 6 | Configurar `id2label` con los nombres reales de clase al guardar el modelo | Media |
| 7 | Sacar el `venv/` y los pesos del control de versiones | Media |

### Reentrenamiento con B2

| # | Tarea |
|---|---|
| 8 | Reentrenar XLM-R con `data/dataset_b2/` y los **pesos nuevos** `[0.9198, 0.9376, 0.9720, 1.2233]` |
| 9 | Evaluar sobre `test.csv` y comparar con el 0.8058 del v1 |
| 10 | Correr `test_adversarial.csv` y comparar con la línea base **48/75** |
| 11 | Exportar `reports/preds_xlmr_b2.csv` con dos columnas: `ID,y_pred` |

---

## Cristian — mBERT

| # | Tarea | Severidad |
|---|---|---|
| 1 | **Entregar los pesos entrenados.** Sin ellos no se puede verificar ni probar robustez | Alta |
| 2 | Corregir `trivial_baselines`: la clase mayoritaria es **0.128**, no 0.087. El recall de esa clase es 1, no su proporción | Alta |
| 3 | Añadir al pipeline el guardado de predicciones en cada corrida. Es la causa de que no se pudiera hacer McNemar | Alta |
| 4 | Añadir un slice de evaluación por emoji en `slices.py` | Media |
| 5 | Reentrenar mBERT con `data/dataset_b2/` y los pesos nuevos |
| 6 | Evaluar sobre `test.csv` y comparar con el 0.7862 del v1 |
| 7 | Correr `test_adversarial.csv` |
| 8 | Exportar `reports/preds_mbert_b2.csv` con `ID,y_pred` |

---

## Willian — coordinación y datos

| # | Tarea | Estado |
|---|---|---|
| 1 | Reparar el léxico de emojis | **Hecho** |
| 2 | Generar el dataset B2 | **Hecho** |
| 3 | Auditoría y comparativa estadística | **Hecho** |
| 4 | Ejecutar `comparar_modelos.py` cuando lleguen las dos predicciones | Pendiente |
| 5 | Recolección real de emojis de amenaza (🔫🔪⚰️): hoy la cobertura es 100% sintética | Pendiente |
| 6 | Recolección dirigida hasta 771 reales por clase | Pendiente |
| 7 | Integrar los tres informes en el documento de la tesina | Pendiente |

---

## Orden y dependencias

```
Julio 1-3  ─┐
Cristian 2  ─┼─→  se pueden hacer YA, en paralelo, sin GPU
Cristian 1  ─┘

Julio 8-11    ─┐
Cristian 5-8  ─┴─→  requieren GPU; ambos con el MISMO dataset y los MISMOS pesos

                    ↓
Willian 4  ─→  comparar_modelos.py  ─→  resultado final de la comparativa
```

**Regla:** los dos reentrenamientos tienen que usar `data/dataset_b2/` y los mismos pesos de clase. Si uno entrena con B2 y el otro con el v1, la comparación no vale.

---

## Qué reportar en la tesina

| Bloque | Contenido |
|---|---|
| Métricas principales | F1-macro sobre `test.csv`, comparables con el v1 |
| Robustez | Resultados sobre `test_adversarial.csv`, **por separado** |
| Comparativa | McNemar pareada con el p-valor real, no dos números sueltos |
| Fairness | FPR por jerga antes y después del B2 |
| Declaración | 1,149 ejemplos sintéticos, 35% del train, generados por plantilla |
