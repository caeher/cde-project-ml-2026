# Dataset v4 — Etapa II + datos reales de X (octubre 2026)

Reconstruir: `python src/data/build_dataset_v4.py`
Sobre el corpus de la Etapa II (repo v3): `python src/data/build_dataset_v4.py --base <ruta>/train_etapa2.csv --salida data/dataset_v4_e2`

## Qué entró

| | Filas |
|---|---|
| Recibidas en `data/new-10-7-2026/` | 4,328 |
| Fuga: ya estaban en **val o test** (todas de `dataset_x2000.csv`: 65 No Tóxico, 15 Amenazas) | −80 |
| Mismo texto con etiqueta distinta entre Cristian y Julio | −6 |
| Duplicados internos | −3 |
| Ya presentes en el train | −168 |
| **Incorporadas** | **4,074** |

Además se quitaron **23 filas del train B2 heredado**: 1 coincidía con val bajo una comparación estricta (sin mayúsculas ni puntuación) y 22 sintéticos coincidían con la batería adversarial.

Los detalles quedan en `reports/v4_filas_con_fuga.csv` y `reports/v4_conflictos_etiqueta.csv`.

## Corrección de etiquetas

**384 filas de `thenewdata_X.csv` se reetiquetaron de Discurso de Odio a Lenguaje Ofensivo.** Eran insultos por afiliación política (subclases «Discriminación política» e «Insulto político»: ARENA, FMLN, Nuevas Ideas).

La guía de anotación (§3.1) es explícita: *«La afiliación política NO es categoría protegida… Lenguaje Ofensivo, no Discurso de Odio. Esta regla no admite excepción.»* Cristian ya etiquetaba ese mismo fenómeno como Ofensivo, y el test no contiene ningún caso político en Discurso de Odio.

Sin esta corrección los datos nuevos **empeoraban el modelo de forma significativa** (F1 test 0.782 → 0.750, McNemar p = 0.024). Con ella, la caída desaparece (p = 0.74).

## Composición final

| Clase | Train v4 | De ellas, nuevas |
|---|---|---|
| No Tóxico | 1,686 | 795 |
| Lenguaje Ofensivo | 2,587 | 1,709 |
| Discurso de Odio | 1,459 | 613 |
| Amenazas/Violencia | 1,612 | 957 |
| **Total** | **7,344** | **4,074** |

Reales: 6,217 · Sintéticos: 1,127. **val (459) y test (460) sin cambios**, verificado por aserción.

Columnas nuevas: `recolector`, `validado` (las nuevas vienen `NO`), `fuera_de_sv` (230 filas que mencionan otro país sin ninguna señal salvadoreña: Colombia, México, Argentina, España…). Se conservan para poder hacer la ablación.

`URL_Original` se eliminó.

## Prueba rápida con modelo lineal (TF-IDF + LinearSVC)

No sustituye el reentrenamiento de RoBERTuito, pero mide la dirección del efecto:

| Train | F1 test | X (n=228) | Facebook (n=232) |
|---|---|---|---|
| B2 (sin nuevos) | 0.7808 | 0.866 | 0.659 |
| v4 (con nuevos) | 0.7733 | **0.889** | **0.611** |

**Los datos nuevos mejoran X y empeoran Facebook.** Son 100 % de X, más largos (165 caracteres contra 90 de Facebook en el test), y el modelo se especializa. Bajar su peso no resuelve el intercambio: con peso 0.25 Facebook ya cae 1.9 puntos.

## Advertencias para la tesina

1. **Las etiquetas son preliminares.** Las 4,074 filas tienen `Validado = NO` y las notas dicen «Etiqueta preliminar; validar contexto». No hubo segundo anotador.
2. **Cada archivo es de una sola clase y se recolectó por búsqueda de palabras clave** (p. ej. «criminales que los maten a todos» → Amenazas). Existe riesgo de que el modelo aprenda el estilo de la consulta en lugar del contenido. La batería adversarial no bajó, lo cual es buena señal, pero conviene declararlo.
3. **No suben Facebook.** El punto débil del sistema sigue igual o peor; lo arreglan datos de Facebook, no más datos de X.
