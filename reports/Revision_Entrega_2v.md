# Revisión de la entrega 2v

**Autor:** Willian Alexander Chávez Servellón
**Fecha:** 12 de septiembre de 2026
**Alcance:** revisión documental de los dos informes nuevos. No incluye reejecución de los modelos.

---

## 0. Qué se pudo revisar y qué no

| | Estado |
|---|---|
| `3 INFORME DE MÉTRICAS mBERT` (Cristian) | Revisado |
| `metricsxlmrV2.pdf` (Julio) | Revisado |
| `metricas-proyecto-ml-colab.zip` | **Sin abrir** (ZIP anidado) |
| `protitpoV2.0` (carpeta de Julio) | **Sin abrir** |
| Reejecución de los modelos | **No realizada** |

El entorno de ejecución quedó inutilizable por una actualización de Windows del 8 de septiembre. Todo lo que sigue proviene de leer los informes y verificar su aritmética interna, más el contraste con las mediciones independientes que sí se hicieron en la verificación del 1 de septiembre.

**Consecuencia:** las cifras nuevas de Cristian (F1 0.7610, batería 120/144) **no están verificadas**. Quedan como declaradas hasta que se pueda volver a correr el modelo.

---

## 1. Cristian — mBERT B2: adoptó B2 y funcionó

Este es el cambio importante de la entrega. En agosto había rechazado B2 por su regla de «si el F1 cae más de 0.02, no se adopta». Ahora lo adoptó y documentó el intercambio de frente.

### 1.1 El intercambio

| | v1 (ckpt-1072) | **B2 (ckpt-1644)** |
|---|---|---|
| F1-macro test | 0.7777 | **0.7610**  (−0.017) |
| Accuracy test | 0.7826 | 0.7674 |
| ECE | 0.157 | 0.164 |
| Batería 75 casos | 45/75 | **64/75** |
| Batería 144 casos | 74/144 * | **120/144** |
| C. Amenazas ofuscadas | 6/11 | **11/11**  (FN = 0) |
| B. Emojis | 7/18 | **16/18** |
| G. Pares mínimos de emoji | 12/35 * | **30/35** |
| Brecha FPR dialectal (D−E) | 0.8571 | **0.0714** |
| A. Ofuscación de groserías | 18/20 * | **12/20** |

\* medido de forma independiente el 1 de septiembre.

Pagó 1,7 puntos de F1-macro y a cambio dejó de perder amenazas ofuscadas, arregló los emojis y cerró casi por completo la brecha dialectal en la batería. Para un sistema de moderación el trato es favorable: perder 10 de 16 amenazas era el problema más grave del v1.

### 1.2 El rebalanceo se aplicó

El informe menciona «masa efectiva ≈ 90 en amenazas sintéticas durante el entrenamiento». Eso es exactamente el rebalanceo B3 que se había propuesto (bajar los sintéticos de Amenazas de 268 a ~90). Es la razón de que ahora el F1 caiga 1,7 puntos en lugar de los 6 del experimento de agosto.

### 1.3 Correcciones pendientes que sí se aplicaron

- **Baseline trivial:** ahora 0.1284, con explicación del redondeo. Corregido.
- **Trazabilidad:** el 0.7862 queda archivado como no reproducible; el 0.7777 como histórico reproducible.
- **Cifras por plataforma:** archiva sus propias 0.8503 / 0.6896 como no reproducibles y publica las oficiales.
- **Zero-shot:** declara explícitamente que no se re-evaluó con B2. Honesto.

---

## 2. Errores en el informe de Cristian

### 2.1 La conclusión sobre McNemar dice lo contrario de lo que muestra el dato

La Tabla 6.5 reporta `mBERT vs XLM-RoBERTa: p = 0.041391, b = 26, c = 44`.

Con **b = 26** (aciertos solo de mBERT) y **c = 44** (aciertos solo de XLM-R), quien gana es **XLM-R**. El propio texto lo dice bien un párrafo antes: *«con XLM-R acertando más instancias en este test»*.

Pero el hallazgo 3 de las conclusiones afirma:

> «La prueba de McNemar confirma superioridad significativa de mBERT B2 frente a MultinomialNB **y frente a XLM-RoBERTa v1**»

Está invertido. La prueba muestra superioridad de XLM-R sobre mBERT B2. Hay que corregirlo antes de que esto llegue a la tesina.

Nota: al bajar mBERT de 0.7777 a 0.7610, la comparación con XLM-R pasó de empate estadístico (p = 0.20 en la verificación independiente) a diferencia significativa (p = 0.041) — **a favor de XLM-R**. Es una consecuencia real de adoptar B2, y debe declararse como tal.

### 2.2 La tabla de familias no suma con el global

Tabla de la batería extendida (n = 144):

| Fam. | mBERT | XLM-R ref. | n |
|---|---|---|---|
| A | 12/20 | 17/20 | 20 |
| B | 16/18 | 6/18 | 18 |
| C | 11/11 | 5/11 | 11 |
| D | FPR 1/14 | 6/14 | 14 |
| E | FPR 0/12 | 0/12 | 12 |
| F | FPR 8/34 | 26/34 | 34 |
| G | 30/35 | 12/35 | 35 |
| **ALL** | **120/144** | **74/144** | 144 |

La columna mezcla dos magnitudes: A, B, C y G son **aciertos**; D, E y F son **falsos positivos** (errores). Sin decirlo en el encabezado.

Sumando tal como está escrito: mBERT da 78, no 120. Convirtiendo D, E y F a aciertos (13 + 12 + 26) sí da 120. Así que la cifra global es correcta, pero la tabla es ilegible sin esa conversión implícita.

**En la columna de XLM-R hay además un error de valor.** Para que el global de 74 cuadre, la celda F debe ser **20/34** de falsos positivos (14 aciertos, que es lo medido de forma independiente). El informe pone **26/34**, que es el número de *aciertos de mBERT* en esa misma fila. Es un valor copiado de una columna a la otra — el mismo tipo de error que ya se había señalado antes.

### 2.3 El sesgo dialectal no mejoró en datos reales

Esta es la observación de fondo. El informe concluye:

> «reduce el sesgo dialectal (FPR gap 0.07 vs 0.86)»

Pero esa cifra viene de los grupos D y E de la **batería sintética**. En la sonda sobre el conjunto de prueba real, el mismo informe reporta:

| | FPR con jerga | FPR sin jerga |
|---|---|---|
| mBERT B2 (Tabla 6.10) | **0.4138** (12/29) | 0.1596 (15/94) |
| mBERT v1 (medido en sept.) | 0.4138 | 0.1596 |

**Idéntico al v1.** La brecha dialectal en datos reales no se movió ni un punto.

Y el hallazgo 5 de sus propias conclusiones lo admite: *«La sonda dialectal muestra FPR elevado en No Tóxico con jerga local (41 % vs. 16 %)»*. O sea, el hallazgo 2 dice que el sesgo se redujo y el 5 dice que sigue igual. Ambos en la misma página.

**Interpretación:** la mejora dialectal aparece donde los datos de evaluación comparten plantillas con los datos de entrenamiento, y no aparece donde no las comparten. El grupo F (falsos amigos dialectales), que es el más independiente de las plantillas, sí mejora de forma genuina (26/34 frente a 17/34 medido en v1) — eso es real. Pero el conjunto de prueba real no refleja ninguna mejora, y es lo que hay que reportar en la tesina.

### 2.4 Texto y tabla se contradicen en los baselines TF-IDF

Página 8. El texto dice:

> «LinearSVC obtiene el mejor F1-macro (0,765), seguido de Logistic Regression (0,758) y MultinomialNB (0,648)»

La tabla inmediatamente debajo dice **0.7482 / 0.7354 / 0.6932**. El texto quedó con los valores del v1 cuando la tabla ya se regeneró con B2. (De paso: los sintéticos también bajaron los baselines lineales, lo cual es coherente con el resto del cuadro.)

### 2.5 La tabla de trazabilidad tiene la columna de checkpoint mal

| F1-macro | Estado | Checkpoint según la tabla | Checkpoint real |
|---|---|---|---|
| 0.7610 | Oficial | checkpoint-1072 | **checkpoint-1644** |
| 0.7777 | Histórico | checkpoint-1072 | checkpoint-1072 ✓ |
| 0.7715 | Solo validación | checkpoint-1072 | es el val del **v1**, no de B2 |

El texto dice que el oficial es ckpt-1644; la tabla dice 1072 en todas las filas. Y el 0.7715 se atribuye a `mbert-sv-b2/train_metrics.json` cuando el propio informe indica que la validación de B2 es 0.756.

### 2.6 Interpretabilidad sigue vacía

Jaccard LIME–SHAP nulo incluso después de alinear subwords WordPiece; pesos globales LIME no exportados. Está mejor documentado que antes, pero el capítulo sigue sin contenido. Conviene retirarlo o reducirlo a una nota metodológica.

---

## 3. Julio — Prototipo V2: un parche, no un modelo

El informe de Julio va por una vía distinta: un pipeline de cuatro niveles que combina reentrenamiento con pesos, umbrales manuales por clase, un filtro de expresiones regulares y un colapso a decisión binaria.

**Resultado que declara:** FPR dialectal de 44,83 % a **14,63 %**.

### 3.1 El filtro de regex es el problema central

Nivel 3: si un texto clasificado como *Lenguaje Ofensivo* contiene alguno de estos patrones —

> `"qué onda"`, `"todo bien"`, `"te quiero"`, `"mi hermano"`, `"gracias"`

— se reasigna forzosamente a **No Tóxico**.

Tres consecuencias:

1. **Es trivialmente evadible.** Basta anteponer «gracias» a cualquier insulto o amenaza para desactivar la moderación. Es una puerta trasera documentada en el propio informe.
2. **La mejora de FPR es circular.** Una regla que solo puede mover predicciones hacia No Tóxico reduce el FPR por construcción. Reportar esa reducción como evidencia de mitigación no demuestra nada sobre el modelo.
3. **Él mismo lo reconoce** en la sección 4 con el ejemplo «Gracias por arruinarme el día, cerote» — pero lo envía igual como solución «en producción».

### 3.2 La comparación no es válida

| | Baseline | Sistema mitigado |
|---|---|---|
| FPR jerga | 44,83 % | 14,63 % |
| Conjunto | n = 29 (test real) | **N = 1050** |

El 44,83 % se midió sobre **29 ejemplos** del test. El 14,63 % se mide sobre un conjunto de **1.050** que no corresponde a ninguna partición del proyecto (train 2.144 / 3.293, val 459, test 460) y que no se documenta ni se entrega. Son denominadores distintos sobre conjuntos distintos: la comparación no se sostiene.

Además, el informe dice que los umbrales se optimizaron «sobre el conjunto de validación» y luego reporta los resultados «en el conjunto de validación dialectal». Si es el mismo conjunto, los números están inflados por construcción.

### 3.3 No reporta F1-macro

La métrica principal del proyecto es **F1-macro ≥ 0.80**. El informe no la reporta en ningún lugar. Da accuracy multiclase (80,22 %) y recalls sueltos, pero no la métrica de decisión. Sin F1-macro no es comparable con nada de lo demás.

### 3.4 Arrastra las cifras incorrectas de la versión anterior

La columna «Baseline XLM-RoBERTa» usa accuracy **81,09 %** y recall de Amenazas **77,38 %**. Los valores verificados son **80,65 %** y **78,31 %**. Son los mismos errores señalados en la revisión del 1 de septiembre, sin corregir.

### 3.5 Los umbrales están subespecificados

| Clase | Umbral |
|---|---|
| No Tóxico | 0.00 |
| Discurso de Odio | 0.36 |
| Lenguaje Ofensivo | 0.45 |
| Amenazas/Violencia | 0.48 |

Con No Tóxico en 0.00 el umbral se cumple siempre. El informe no dice cómo se resuelve el caso en que varias clases superan su umbral, ni en qué orden se evalúan. Tal como está, la regla de decisión no es reproducible.

### 3.6 Propone como trabajo futuro lo que ya existe

La fase 1 de su hoja de ruta es:

> «Aumento Sintético de Datos Dialectales: crear un corpus suplementario con N ≥ 5.000 ejemplos donde la jerga local esté etiquetada correctamente según el contexto.»

Eso es exactamente el dataset B2, entregado en agosto, y que Cristian acaba de usar con éxito. Julio construyó un parche heurístico para resolver un problema que ya tenía solución de datos disponible.

### 3.7 Lenguaje impreciso

El informe habla de «en producción», «desplegada», «Sistema Mitigado v1.4». No hay ningún sistema en producción. Para una tesina conviene ajustar el registro a lo que realmente existe: un prototipo experimental.

---

## 4. El contraste entre los dos enfoques

Los dos atacaron el mismo problema —el sesgo dialectal— por caminos opuestos, y el resultado es instructivo:

| | Cristian | Julio |
|---|---|---|
| Enfoque | Reentrenar con datos (B2 + reponderación) | Umbrales + reglas regex post-hoc |
| ¿El modelo aprendió? | Sí, en la capa de representación | No, es una capa externa |
| ¿Evadible? | No más que cualquier clasificador | Sí, con una palabra |
| ¿Mejora verificable? | Parcial: batería sí, test real no | No comparable |
| Costo declarado | −1,7 pts de F1-macro | No reporta F1-macro |
| Reproducible | Sí (checkpoint, semilla, hash) | No (conjunto N=1050 no entregado) |

**El enfoque de Cristian es el que debe ir a la tesina.** El de Julio sirve como sección de «alternativas consideradas y descartadas», que es un aporte legítimo si se presenta así — su propio análisis crítico de limitaciones (sección 4 de su informe) está bien escrito y es honesto.

---

## 5. Acciones

### Cristian

| # | Tarea | Severidad |
|---|---|---|
| 1 | Corregir el hallazgo 3: la prueba de McNemar favorece a **XLM-R**, no a mBERT | Crítica |
| 2 | Separar aciertos de FPR en la tabla de familias, o etiquetar la magnitud de cada columna | Alta |
| 3 | Corregir la celda F de XLM-R: 20/34, no 26/34 | Alta |
| 4 | Resolver la contradicción entre los hallazgos 2 y 5 sobre el sesgo dialectal; declarar que la mejora se observa en la batería y **no** en el test real | Crítica |
| 5 | Actualizar el texto de los baselines TF-IDF (0.7482 / 0.7354 / 0.6932) | Media |
| 6 | Corregir la columna de checkpoint en la tabla de trazabilidad (1644, no 1072) y la fila de 0.7715 | Media |
| 7 | Retirar o reducir el capítulo de interpretabilidad | Media |

### Julio

| # | Tarea | Severidad |
|---|---|---|
| 1 | Reportar **F1-macro** sobre `test.csv` (n = 460), con y sin el pipeline de mitigación | Crítica |
| 2 | Documentar y entregar el conjunto N = 1050, o rehacer la comparación sobre el test real (n = 29 con jerga) | Crítica |
| 3 | Separar el conjunto de ajuste de umbrales del conjunto de evaluación | Crítica |
| 4 | Corregir el baseline: accuracy 0.8065 y recall Amenazas 0.7831 | Alta |
| 5 | Especificar la regla de decisión de los umbrales (orden, desempate, qué significa 0.00) | Alta |
| 6 | Cuantificar la evadibilidad del filtro regex: cuántas amenazas de la batería pasan si se les antepone «gracias» | Alta |
| 7 | Corregir `id2label` en el `config.json` entregado (pendiente desde agosto) | Media |
| 8 | Reencuadrar «producción / desplegado» como prototipo experimental | Media |

### Willian

| # | Tarea |
|---|---|
| 1 | Reejecutar mBERT B2 y XLM-R cuando el entorno vuelva, y verificar el F1 0.7610 y la batería 120/144 |
| 2 | Correr la batería de 144 casos sobre el pipeline mitigado de Julio, incluyendo variantes con marcadores afectivos inyectados |
| 3 | Rehacer la comparativa pareada con el B2 oficial y confirmar el p = 0.041 |
| 4 | Medir el sesgo dialectal en datos reales recolectados, no sintéticos — es el punto ciego que ninguna de las dos soluciones resuelve |

---

## 6. Resumen en una línea

Cristian adoptó B2 y el modelo mejoró de verdad donde importa (cero amenazas perdidas, emojis resueltos), a costa de 1,7 puntos de F1 y de perder el empate estadístico frente a XLM-R; su informe tiene cuatro errores corregibles, uno de los cuales invierte una conclusión. Julio resolvió el mismo problema con un filtro de expresiones regulares que se evade escribiendo «gracias», sobre un conjunto de evaluación que no existe en el proyecto, y sin reportar la métrica principal.
