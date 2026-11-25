# Fe de erratas — Reporte de la Etapa II

Correcciones de redacción listas para pegar en el reporte (el archivo del reporte está en el repo del equipo, rama v3). Los resultados no cambian; cambian las afirmaciones que contradicen las propias tablas.

## Graves

1. **§12.2 y Tabla 13 — modelo individual.** El IC del modelo individual es [0.7912, 0.8610]: el extremo inferior **no** supera 0.80.
   - Texto sugerido: «El extremo inferior del intervalo del ensemble se situó en 0.8191, por encima de 0.80; el del modelo individual, en 0.7912, no lo alcanza y el intervalo cruza la meta.»
   - Tabla 13: cambiar «¿Meta con IC?» del modelo individual de «Sí» a «No» (mismo criterio que TwitterXLM-R, 0.7940, que figura como «No»).
2. **§12.4 — McNemar.** Con p = 0.2820 (vs XLM-R v1), 0.0026 (vs mBERT B2) y 0.0567 (vs XLM-R mitigado), solo una comparación es significativa a α = 0.05.
   - Texto sugerido: «La diferencia es significativa frente a mBERT B2 (p = 0.0026), marginal y no significativa frente a XLM-R mitigado (p = 0.0567) y no concluyente frente a XLM-R v1 (p = 0.2820).»
3. **§12.3 — prosa vs Tabla 14.** La prosa (Discurso de Odio 0.8308; Amenazas 0.8488; «las cuatro clases superaron 0.83») contradice la Tabla 14 (0.8020 y 0.8293).
   - Corrección: indicar a qué modelo corresponde cada cifra (la prosa parece describir el ensemble y la tabla el modelo individual) y unificar. Esto no se pudo verificar sin las predicciones de la Etapa II: recalcular el F1 por clase del ensemble y del individual desde sus probabilidades y copiar esos valores.

## Menores

4. Tabla 8: «0 épocas solo reales» contra «tres» en el texto. Unificar.
5. Tabla 16 vs Tabla 20: batería 125 vs 127. Recalcular desde las predicciones.
6. Semilla 2026: 0.8555 (tabla) vs 0.8562 (texto). Recalcular.
7. Tabla 11 dice «seis» y tiene cuatro filas.
8. Los cortes de la Tabla 21 no suman 460.

## Nota adicional (hallazgo del 7 de octubre)

La batería de 144 de la Etapa II (127/144) pudo estar favorecida por 20 filas sintéticas del train que repetían una frase de la batería con otro emoji (`data/history/v1.3.1/README.md`). El test no tenía solape. Al quitarlas y reentrenar con la misma receta, la línea base dio 122/144 y F1 test 0.8358 (no 0.8529): ver `reports/improvement/Resultado_reentrenamiento_v4.md`.
