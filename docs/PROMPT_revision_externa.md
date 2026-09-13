# Prompt para revisión externa de la entrega 2v

> Copiar todo lo que sigue y pasárselo al revisor junto con acceso a la carpeta del proyecto.

---

## Contexto: qué estamos haciendo

Somos tres estudiantes de la Universidad de El Salvador desarrollando un trabajo de graduación de maestría. El objetivo es **clasificar automáticamente toxicidad y discurso de odio en publicaciones de redes sociales salvadoreñas** (X/Twitter y Facebook), mediante *fine-tuning* de dos modelos multilingües preentrenados.

**Meta declarada del proyecto:** F1-macro ≥ 0.80 sobre el conjunto de prueba.

### Las cuatro clases (son exactamente cuatro, no hay más)

| Label | Clase |
|---|---|
| 0 | No Tóxico |
| 1 | Lenguaje Ofensivo |
| 2 | Discurso de Odio |
| 3 | Amenazas/Violencia |

### Reparto

| Persona | Responsabilidad |
|---|---|
| Cristian Escalante | mBERT (`bert-base-multilingual-cased`, **cased** obligatorio) |
| Julio De La Quadra | XLM-RoBERTa (`xlm-roberta-base`) |
| Willian Chávez | Datos, normalización, auditoría y comparativa estadística |

### Particiones

| Split | n | Nota |
|---|---|---|
| train v1 | 2,144 | Solo datos reales |
| train B2 | 3,293 | 2,144 reales + 1,149 sintéticos dirigidos |
| val | 459 | Idéntico byte a byte entre v1 y B2 |
| test | 460 | Idéntico byte a byte entre v1 y B2 |

`val` y `test` se mantuvieron intactos deliberadamente para que las métricas sean directamente comparables entre versiones.

### Contrato de inferencia

- `max_length = 128`
- Columna de entrada: `texto_modelo`
- Normalizador: `normalize_for_model` v1.1
- Semilla: 42

### Qué es el dataset B2

Ampliación del corpus con 1,149 ejemplos sintéticos generados por plantilla, para cerrar cuatro huecos detectados en una auditoría previa:

1. **Atajo emoji ⇒ tóxico.** El 89 % de los textos con emoji del corpus v1 pertenecen a *Lenguaje Ofensivo*, así que los modelos aprendieron «hay emoji, es ofensivo» en vez del significado de cada emoji.
2. **Emojis de ataque nunca vistos.** 🔫 🔪 ⚰️ 🐒 🧼 tenían cero apariciones en v1.
3. **Amenazas ofuscadas.** «Te voy a m4t4r» se clasificaba como ofensivo, no como amenaza.
4. **Sesgo dialectal.** Frases inofensivas con jerga salvadoreña (*pajero* = mentiroso, *chucho* = perro, *pisto* = dinero, *cerote* = amigo) se marcaban como tóxicas.

### Qué es la batería adversarial

`data/dataset_b2/test_adversarial.csv`, 144 casos con etiqueta esperada conocida, agrupados en siete familias. **Es diagnóstica, no sustituye al F1-macro oficial sobre `test.csv`.**

| Grupo | n | Qué mide |
|---|---|---|
| A | 20 | Ofuscación de groserías (`p*ta`, `put@s`, `m13rda`) |
| B | 18 | Emojis del catálogo |
| C | 11 | Amenazas ofuscadas (`m4t4r`, «dar piso») |
| D | 14 | Jerga salvadoreña inofensiva |
| E | 12 | Control: mismo contenido en español estándar |
| F | 34 | Falsos amigos dialectales + 4 contrastes agresivos |
| G | 35 | Pares mínimos de emoji (mismo texto, distinto emoji) |

---

## Tu tarea

Revisar la entrega del 12 de septiembre de 2026, que está en `Métricas de Evaluación/2v/`:

| Archivo | Autor |
|---|---|
| `Para el modelo mBERT-…zip` → `3 INFORME DE MÉTRICAS mBERT …pdf` + `metricas-proyecto-ml-colab.zip` | Cristian |
| `PrototipoV2-…zip` → `metricsxlmrV2.pdf` + carpeta `protitpoV2.0` | Julio |

**Hay ZIP anidados que aún no se han abierto.** Empezá por ahí: el código y los pesos están adentro.

### Lo esencial: no creas las cifras, reprodúcelas

El problema recurrente de este proyecto ha sido que los informes publican números que no coinciden con los modelos entregados. Ya se detectaron, en entregas anteriores:

- Una matriz de confusión que contradecía su propia tabla por clase.
- Un informe que describía una corrida cuyos pesos nunca se entregaron.
- Valores de una columna copiados a la columna de otro modelo.
- Un FPR escrito a mano en el código en lugar de calculado.

Así que: **cargá los pesos, corré la inferencia sobre `test.csv` y comparalo con lo publicado.** Todo lo demás es secundario.

---

## Línea base verificada (reejecutada de forma independiente el 1 de septiembre de 2026)

Estas cifras se obtuvieron cargando los pesos entregados y corriendo el *forward pass*. Son el punto de referencia contra el cual comparar. Si tu reejecución no las reproduce, el problema es tu configuración, no estos números.

### Globales sobre `test.csv` (n = 460)

| | mBERT v1 | XLM-R v1 |
|---|---|---|
| F1-macro | **0.7777** | **0.8058** |
| Accuracy | 0.7826 | 0.8065 |
| Aciertos | 360/460 | 371/460 |

### Por clase

| Clase | F1 mBERT | F1 XLM-R | Soporte |
|---|---|---|---|
| No Tóxico | 0.8136 | 0.8155 | 123 |
| Lenguaje Ofensivo | 0.7951 | 0.8061 | 159 |
| Discurso de Odio | 0.7461 | 0.8041 | 95 |
| Amenazas/Violencia | 0.7561 | 0.7975 | 83 |

### Matrices de confusión (fila = real, columna = predicho)

**mBERT v1**

| | NT | LO | DO | AV |
|---|---|---|---|---|
| No Tóxico | 96 | 14 | 7 | 6 |
| Lenguaje Ofensivo | 9 | 130 | 13 | 7 |
| Discurso de Odio | 6 | 11 | 72 | 6 |
| Amenazas/Violencia | 2 | 13 | 6 | 62 |

**XLM-R v1**

| | NT | LO | DO | AV |
|---|---|---|---|---|
| No Tóxico | 95 | 16 | 7 | 5 |
| Lenguaje Ofensivo | 9 | 133 | 8 | 9 |
| Discurso de Odio | 5 | 11 | 78 | 1 |
| Amenazas/Violencia | 1 | 11 | 6 | 65 |

### Cortes

| Corte | n | mBERT | XLM-R |
|---|---|---|---|
| Plataforma X | 228 | 0.8386 | 0.8673 |
| Plataforma Facebook | 232 | 0.6727 | 0.7154 |
| FPR No Tóxico **con** jerga | 29 | 0.4138 | 0.4483 |
| FPR No Tóxico **sin** jerga | 94 | 0.1596 | 0.1596 |

### Batería adversarial (144 casos), modelos v1

| Grupo | n | mBERT | XLM-R |
|---|---|---|---|
| A | 20 | 18 | 17 |
| B | 18 | 7 | 6 |
| C | 11 | 6 | 5 |
| D | 14 | 2 | 8 |
| E | 12 | 12 | 12 |
| F | 34 | 17 | 14 |
| G | 35 | 12 | 12 |
| **Global** | 144 | **74** | **74** |

### Comparativa pareada v1

```
McNemar exacto:  b = 25 (solo mBERT), c = 36 (solo XLM-R),  p = 0.20
Δ F1-macro (XLM-R − mBERT) = +0.0281,  IC 95 % bootstrap [−0.0068, +0.0627]
→ empate estadístico
```

### Pisos triviales

| Baseline | F1-macro |
|---|---|
| Clase mayoritaria | **0.1284** |
| Azar uniforme / estratificado | 0.2500 |

El de clase mayoritaria es 0.1284, no 0.087. Se calcula `F1_mayoritaria = 2p/(1+p)` con `p = 0.3457`, dividido entre 4 clases. Un error anterior usaba la prevalencia como si fuera el F1.

---

## Cifras nuevas que hay que verificar

### Cristian — mBERT B2 (checkpoint-1644)

| Afirmación | Valor publicado |
|---|---|
| F1-macro test | 0.7610 |
| Accuracy test | 0.7674 |
| IC bootstrap | [0.7179, 0.7981] |
| ECE | 0.1640 |
| F1-macro validación | 0.756 |
| Batería 144 | 120/144 |
| Batería 75 | 64/75 |
| Grupo C (amenazas ofuscadas) | 11/11, FN = 0 |
| Grupo B (emojis) | 16/18 |
| Grupo G | 30/35 |
| Grupo A | 12/20 |
| Brecha FPR dialectal (D−E) | 0.0714 |
| McNemar vs XLM-R | b = 26, c = 44, p = 0.041391 |
| Baselines TF-IDF (reentrenados con B2) | LinearSVC 0.7482 · LogReg 0.7354 · MNB 0.6932 |

Dice haber entrenado con «masa efectiva ≈ 90 en amenazas sintéticas», es decir reponderando los sintéticos de Amenazas a la baja.

### Julio — Prototipo V2

| Afirmación | Valor publicado |
|---|---|
| FPR jerga, baseline | 44.83 % |
| FPR jerga, sistema mitigado | 14.63 % |
| Recall Discurso de Odio | 81.05 % |
| Recall Amenazas/Violencia | 80.72 % |
| Accuracy global multiclase | 80.22 % |
| Conjunto de evaluación | N = 1050 |

Su pipeline tiene cuatro niveles: reentrenamiento con `WeightedTrainer`, umbrales manuales por clase (`No Tóxico 0.00`, `Odio 0.36`, `Ofensivo 0.45`, `Amenazas 0.48`), un filtro de expresiones regulares, y colapso a decisión binaria.

El filtro regex reasigna a **No Tóxico** cualquier texto clasificado como *Lenguaje Ofensivo* que contenga: `"qué onda"`, `"todo bien"`, `"te quiero"`, `"mi hermano"`, `"gracias"`.

---

## Comprobaciones concretas

### Prioridad 1 — reproducción

1. Abrí los ZIP anidados. Listá qué hay: pesos, notebooks, `config.json`, `MANIFEST.json`, CSV de métricas.
2. Cargá cada modelo y corré la inferencia sobre `test.csv` con `max_length=128` y la columna `texto_modelo`.
3. Confirmá o refutá: mBERT B2 = 0.7610 y XLM-R = 0.8058.
4. Regenerá las matrices de confusión y las métricas por clase desde tus propias predicciones.
5. Corré la batería de 144 casos en ambos. Confirmá o refutá el 120/144.
6. Exportá `ID,y_pred` de cada modelo y corré McNemar pareado. Confirmá o refutá `b=26, c=44, p=0.041`.

### Prioridad 2 — errores ya sospechados (confirmalos o descartalos)

**En el informe de Cristian:**

- El hallazgo 3 de las conclusiones afirma «superioridad significativa de mBERT B2 frente a XLM-RoBERTa». Con `b=26` y `c=44`, ¿a favor de quién va realmente la prueba?
- El hallazgo 2 dice que B2 «reduce el sesgo dialectal (FPR gap 0.07 vs 0.86)», pero la Tabla 6.10 reporta FPR con jerga 0.4138 y sin jerga 0.1596 sobre el test real — idéntico al v1. ¿Mejoró el sesgo dialectal en datos reales o solo en la batería sintética?
- La tabla de familias mezcla aciertos (A, B, C, G) con falsos positivos (D, E, F) sin indicarlo. Verificá que las columnas sumen al global declarado. Revisá específicamente la celda del grupo F en la columna de XLM-R.
- El texto de los baselines TF-IDF cita 0.765 / 0.758 / 0.648 mientras la tabla de la misma página dice 0.7482 / 0.7354 / 0.6932.
- En la tabla de trazabilidad, la columna de checkpoint dice `checkpoint-1072` en todas las filas, pero el oficial es `checkpoint-1644`.
- El capítulo de interpretabilidad: Jaccard LIME–SHAP nulo y pesos globales LIME no exportados. ¿Queda algo de contenido?

**En el informe de Julio:**

- ¿De dónde sale el conjunto `N = 1050`? No corresponde a ninguna partición del proyecto (2,144 / 3,293 / 459 / 460). ¿Está entregado? ¿Es reproducible?
- El 44.83 % baseline se midió sobre n = 29. El 14.63 % sobre N = 1050. ¿Es válida esa comparación?
- Dice que optimizó los umbrales «sobre el conjunto de validación» y luego reporta resultados «en el conjunto de validación dialectal». ¿Ajustó y evaluó sobre el mismo conjunto?
- **No reporta F1-macro en ningún lugar**, que es la métrica principal del proyecto. Calculala vos.
- Cita como baseline accuracy 81.09 % y recall de Amenazas 77.38 %. Los valores verificados son 80.65 % y 78.31 %. ¿Corrigió o arrastró el error?
- Con `No Tóxico` en umbral 0.00, esa condición se cumple siempre. ¿Cómo se resuelve el empate cuando varias clases superan su umbral? ¿Está especificado?
- **Prueba de evadibilidad:** tomá los casos de amenaza de la batería (grupo C y los de amenaza del grupo G), anteponeles `"gracias, "` y pasalos por el pipeline completo. Contá cuántas amenazas se reclasifican como No Tóxico. Reportá el número.
- ¿El `config.json` entregado tiene `id2label` con los nombres reales de clase o sigue con `LABEL_0`…`LABEL_3`? Esta corrección está pendiente desde agosto.

### Prioridad 3 — juicio metodológico

- Los sintéticos de B2 se generaron por plantilla. Los grupos D y E de la batería vienen de plantillas emparentadas. ¿Cuánto de la mejora de B2 es generalización real y cuánto es memorización de plantillas? El grupo F es el más independiente: comparalo aparte.
- Verificá si hay solapamiento textual entre `train` de B2 y la batería adversarial. En agosto se detectaron 7 filas idénticas.
- ¿El enfoque de Julio (reglas post-hoc) y el de Cristian (reentrenamiento con datos) son comparables? ¿Cuál corresponde reportar como resultado del proyecto y cuál como alternativa descartada?

---

## Notas técnicas

- Si no tenés PyTorch disponible, se puede hacer el *forward pass* en NumPy leyendo `model.safetensors` directamente. Hay implementaciones ya hechas en `src/audit/mbert_numpy.py` y `src/audit/xlmr_numpy.py`, validadas contra las métricas oficiales.
- mBERT usa posiciones absolutas `0..T-1`, `token_type_embeddings[0]`, LayerNorm con `eps=1e-12` guardado como `gamma`/`beta`, y cabeza `pooler → tanh → classifier`.
- XLM-RoBERTa desplaza las posiciones: `pos = cumsum(mask)*mask + pad_token_id`, `eps=1e-5`, y usa `RobertaClassificationHead` (`dense → tanh → out_proj`) sobre el token `<s>`.

---

## Qué entregar

Un informe que contenga:

1. **Tabla de contraste**, fila por fila: cifra publicada · cifra reproducida · diferencia. Marcá cada una como reproducible o no reproducible.
2. **Lista de errores encontrados**, con la evidencia aritmética o el fragmento de código que lo demuestra. Distinguí entre error de transcripción, error de cálculo y conclusión incorrecta.
3. **Resultado de la prueba de evadibilidad** del filtro regex de Julio.
4. **Tabla de correcciones pendientes separada por persona**, con severidad.
5. **Tu recomendación** sobre qué modelo y qué cifras deben ir a la tesina.

No hace falta suavizar los hallazgos. El propósito es que lo que se escriba en el documento final sea defendible ante un tribunal.
