# Auditoría de la entrega 2v — reejecución independiente de los modelos

**Autor:** Willian Alexander Chávez Servellón
**Fecha:** 12 de septiembre de 2026
**Alcance:** los dos informes de la entrega 2v, sus ZIP anidados y los pesos entregados.
**Método:** no se aceptó ninguna cifra publicada. Se abrieron los ZIP, se cargaron los cuatro
checkpoints y se corrió el *forward pass* sobre `test.csv`, `val.csv` y la batería adversarial.

---

## 0. Condiciones de la reejecución

| | |
|---|---|
| Entorno | WSL2 · Python 3.10.12 · PyTorch 2.8.0+cu128 · transformers 5.17.0 · GPU RTX 4060 |
| Contrato | `max_length = 128`, columna `texto_modelo`, semilla 42 |
| Scripts | `src/audit/reproducir_2v.py`, `metricas_2v.py`, `bateria_2v.py`, `pipeline_julio.py`, `sonda_ofuscacion_emoji.py` |
| Artefactos | `reports/v2_auditoria/` (logits, predicciones, manifiesto de hashes) |

Checkpoints auditados, con el SHA-256 de `model.safetensors`:

| Alias | Autor | Ruta | SHA-256 (12 primeros) |
|---|---|---|---|
| `mbert_v1` | Cristian | `Pesos del modelo/mbert-sv-audit.zip` | `b2de91405b7c` |
| `mbert_b2` | Cristian | `2v/…/metricas-proyecto-ml/models/mbert-sv` | `7a3ab6c53223` |
| `xlmr_v1` | Julio | `Para modelo XLMR/…/modelo_entrenado` | `574a513b7f9e` |
| `xlmr_mit` | Julio | `2v/…/prototipoV2/…/modelo_mitigado` | `b0cd9cca4ce8` |

**Verificación previa de los datos.** Los CSV que usó Cristian son byte a byte los que se le
entregaron: `train.csv`, `val.csv`, `test.csv`, `metadata.json` y `lexicon_emojis.csv` tienen
hash idéntico al de `data/dataset_b2/`. Su train es de 3,293 filas. Ese punto queda cerrado.
Julio, en cambio, **no usó el dataset B2**: su `train_mitigado.csv` tiene 2,165 filas
(el train v1 de 2,144 más 21 añadidas). Volveré sobre esas 21 en la sección 4.1.

---

## 1. Resultado en una línea

De las dos entregas, **una reproduce todas sus cifras y la otra no reproduce ninguna de las
tres que declara como resultado**.

Cristian publicó 0.7610 de F1-macro y la reejecución da 0.7610. Todas sus tablas cuadran al
cuarto decimal. Sus errores son de redacción, no de medición: cuatro, uno de los cuales
invierte una conclusión.

Julio publicó accuracy 80.22 %, recall de Odio 81.05 % y recall de Amenazas 80.72 % sobre un
conjunto que llama «N = 1050». Ese conjunto no existe en el proyecto, sus propias salidas de
notebook muestran soporte 460, y **ninguna combinación de umbrales sobre los pesos que
entregó reproduce esa terna**. Además su modelo fue entrenado con 21 textos del conjunto de
prueba, y su filtro de reglas se desactiva escribiendo «gracias».

---

## 2. Tabla de contraste: publicado contra reproducido

### 2.1 Cristian — mBERT B2 (`checkpoint-1644`)

| Cifra | Publicado | Reproducido | Δ | Estado |
|---|---|---|---|---|
| F1-macro test | 0.7610 | **0.7610** | 0.0000 | reproducible |
| Accuracy test | 0.7674 | **0.7674** | 0.0000 | reproducible |
| IC bootstrap 95 % | [0.7179, 0.7981] | [0.7172, 0.7983] | ±0.0007 | reproducible (semilla distinta) |
| ECE | 0.1640 | **0.1640** | 0.0000 | reproducible |
| F1-macro validación | 0.756 | **0.7560** | 0.0000 | reproducible |
| F1 No Tóxico | 0.7837 | **0.7837** | 0.0000 | reproducible |
| F1 Lenguaje Ofensivo | 0.7925 | **0.7925** | 0.0000 | reproducible |
| F1 Discurso de Odio | 0.7330 | **0.7330** | 0.0000 | reproducible |
| F1 Amenazas/Violencia | 0.7349 | **0.7349** | 0.0000 | reproducible |
| Plataforma X | 0.8190 | **0.8190** | 0.0000 | reproducible |
| Plataforma Facebook | 0.6648 | **0.6648** | 0.0000 | reproducible |
| FPR No Tóxico con jerga | 0.4138 | **0.4138** (12/29) | 0.0000 | reproducible |
| FPR No Tóxico sin jerga | 0.1596 | **0.1596** (15/94) | 0.0000 | reproducible |
| Batería 75 casos, B2 | 64/75 | **64/75** | 0 | reproducible |
| Batería 75 casos, v1 | 45/75 | **45/75** | 0 | reproducible |
| Batería 144 casos, B2 | 120/144 | **120/144** | 0 | reproducible (ver 3.2) |
| Batería 144 casos, v1 | 69/144 | **69/144** | 0 | reproducible (ver 3.2) |
| Grupo C, amenazas ofuscadas | 11/11, FN = 0 | **11/11, FN = 0** | 0 | reproducible |
| Grupo B, emojis | 16/18 | **16/18** | 0 | reproducible |
| Grupo A, ofuscación | 12/20 | **12/20** | 0 | reproducible |
| Brecha FPR dialectal (D − E) | 0.0714 | **0.0714** | 0.0000 | reproducible |
| McNemar vs XLM-R v1 | b = 26, c = 44, p = 0.041391 | **b = 26, c = 44, p = 0.041391** | 0 | reproducible |
| Baseline LinearSVC | 0.7482 | **0.7482** | 0.0000 | reproducible |
| Baseline LogisticRegression | 0.7354 | **0.7354** | 0.0000 | reproducible |
| Baseline MultinomialNB | 0.6932 | **0.6932** | 0.0000 | reproducible |
| Piso clase mayoritaria | 0.1284 | **0.1284** | 0.0000 | reproducible |

**26 de 26 cifras reproducibles.** Es la primera entrega del proyecto en la que ocurre.

### 2.2 Julio — Prototipo V2 (`modelo_mitigado`)

| Cifra | Publicado | Reproducido | Estado |
|---|---|---|---|
| FPR jerga, baseline | 44.83 % | **44.83 %** (13/29, `xlmr_v1`) | reproducible |
| FPR «sistema mitigado» | 14.63 % | 14.63 % pero **no es FPR de jerga**: es el FPR binario sobre los 123 No Tóxico completos | no comparable |
| FPR de jerga del sistema mitigado | no reportado | **31.03 %** (9/29) | — |
| Recall Discurso de Odio | 81.05 % | **82.11 %** (78/95) con sus umbrales · 80.00 % en argmax | no reproducible |
| Recall Amenazas/Violencia | 80.72 % | **81.93 %** (68/83) | no reproducible |
| Accuracy global multiclase | 80.22 % | **78.70 %** (362/460) con sus umbrales · 78.91 % en argmax | no reproducible |
| Conjunto de evaluación | N = 1050 | **n = 460** (el test del proyecto) | cifra inventada |
| Baseline accuracy | 81.09 % | **80.65 %** (371/460) | no reproducible |
| Baseline recall Amenazas | 77.38 % | **78.31 %** (65/83) | no reproducible |
| Baseline recall Odio | 82.11 % | **82.11 %** | reproducible |
| **F1-macro del sistema** | **no reportado** | **0.7887** (argmax) · **0.7837** (pipeline completo) | — |
| F1-macro del baseline XLM-R v1 | no reportado | **0.8058** | — |

**3 de 11 cifras reproducibles.** Las tres que declara como resultado del trabajo —
accuracy 80.22 %, recall 81.05 % y 80.72 % — no salen de los pesos que entregó.

Para descartar que fuera un problema de configuración por mi parte, hice una búsqueda
exhaustiva: recorrí las 884,736 combinaciones de umbrales `(T₁, T₂, T₃)` en una rejilla de
paso 0.01 sobre `[0.00, 0.95]` aplicadas a los logits del modelo entregado. **Ninguna**
reproduce simultáneamente 369/460 aciertos, 77/95 de recall en Odio y 67/83 en Amenazas.
Sus umbrales publicados (0.45 / 0.36 / 0.48) dan 362, 78 y 68.

---

## 3. Errores encontrados en el informe de Cristian

Cuatro. Los ordeno por gravedad. Ninguno afecta a las mediciones; los cuatro son de
transcripción o de lectura del dato.

### 3.1 Conclusión invertida sobre McNemar — **crítico**

El hallazgo 3 dice:

> «La prueba de McNemar confirma superioridad significativa de mBERT B2 frente a
> MultinomialNB **y frente a XLM-RoBERTa v1** (α = 0,05)»

La prueba reproducida da `b = 26, c = 44, p = 0.041391`. En la convención de la propia tabla,
`b` son los aciertos exclusivos de mBERT y `c` los de XLM-R. Con `c > b` el signo va **a favor
de XLM-R**. El texto de la sección 6 lo dice correctamente («con XLM-R acertando más
instancias en este test»); la conclusión lo dice al revés.

La lectura correcta es incómoda pero hay que escribirla: al adoptar B2, mBERT pasó de estar
empatado con XLM-R (p = 0.20 con el v1) a estar **significativamente por debajo** (p = 0.041).
El Δ F1-macro lo confirma:

```
XLM-R v1 − mBERT v1 : +0.0281   IC95 [-0.0075, +0.0625]   incluye 0  -> empate
XLM-R v1 − mBERT B2 : +0.0448   IC95 [+0.0080, +0.0807]   NO incluye 0 -> XLM-R superior
```

### 3.2 Las dos columnas de la tabla de familias vienen de dos baterías distintas — **crítico**

Esto no se había detectado antes y es más grave que el error de celda que se sospechaba.

En su ZIP hay un fichero `data/processed/test_adversarial_144.csv` que Cristian **generó él
mismo** con `scripts/build_adversarial_144.py`. Tiene los mismos siete grupos y los mismos
tamaños que la batería entregada, pero **no es la misma batería**:

| | Batería entregada | Batería de Cristian |
|---|---|---|
| Textos coincidentes | — | 78 de 144 |
| Grupo F, etiquetas esperadas | 30 × clase 0 + 4 × clase 1 | 34 × clase 0 |
| Grupo G, etiquetas esperadas | 19/4/6/6 | 20/2/2/11 |

Corrí ambas. Sobre **su** batería, sus cifras salen exactas (mBERT B2 = 120/144, v1 = 69/144).
Sobre la **entregada**, mBERT B2 también da 120/144 pero con F y G intercambiados
(F = 30/34, G = 26/35 en lugar de F = 26/34, G = 30/35), y el v1 da **74/144**, no 69.

El problema es que su columna de XLM-R sí está medida sobre la batería **entregada**: los
valores A 17, B 6, C 5, D 6/14 de FPR, E 0/12 y el global 74/144 coinciden exactamente con mi
reejecución sobre la batería oficial. Es decir, **la tabla compara mBERT medido en una batería
contra XLM-R medido en otra**.

Y dentro de esa misma fila hay además el error de celda que ya se sospechaba: el grupo F de
XLM-R dice **26/34** de falsos positivos. El valor correcto es **20/34** en la batería
entregada y **14/34** en la suya. El 26 es el número de *aciertos de mBERT* en esa misma fila,
copiado de una columna a la otra.

Añado que la tabla mezcla dos magnitudes sin decirlo: A, B, C y G son aciertos; D, E y F son
falsos positivos. Sumada tal como está escrita da 78, no 120.

### 3.3 El sesgo dialectal no mejoró en datos reales — **crítico**

El hallazgo 2 dice que B2 «reduce el sesgo dialectal (FPR gap 0.07 vs. 0.86)». El hallazgo 5,
tres párrafos después, dice que «la sonda dialectal muestra FPR elevado en No Tóxico con jerga
local (41 % vs. 16 %)». Los dos son ciertos y hablan de cosas distintas:

| | mBERT v1 | mBERT B2 |
|---|---|---|
| Brecha D − E en la batería sintética | 0.8571 | **0.0714** |
| FPR con jerga en `test.csv` (n = 29) | 0.4138 | **0.4138** |
| FPR sin jerga en `test.csv` (n = 94) | 0.1596 | **0.1596** |

En datos reales la brecha **no se movió ni un punto**. Los grupos D y E de la batería salen de
plantillas emparentadas con las que generaron los sintéticos de B2; ahí la mejora es casi total.
En el test real, donde no hay parentesco de plantilla, no hay mejora.

Dos matices a favor de Cristian. Primero: el grupo F (falsos amigos dialectales) es el más
independiente de las plantillas y ahí la mejora sí es genuina — 4/30 falsos positivos frente a
17/30 del v1. Segundo: en mi sonda dirigida, construida hoy y que ningún modelo pudo haber
visto, la brecha de B2 es **−0.10** frente a **+0.40** del v1 (sección 5.4). La mejora de
representación existe; lo que no existe es en el test real, y es eso lo que hay que declarar.

### 3.4 Errores menores

| # | Dónde | Qué dice | Qué debe decir |
|---|---|---|---|
| a | Texto de baselines, p. 8 | LinearSVC 0,765 · LogReg 0,758 · MNB 0,648 | 0.7482 · 0.7354 · 0.6932 (la tabla de la misma página ya está bien) |
| b | Tabla de trazabilidad | `checkpoint-1072` en las tres filas | el oficial es `checkpoint-1644`; solo la fila histórica de 0.7777 es 1072 |
| c | Tabla de trazabilidad, fila 0.7715 | atribuida a `mbert-sv-b2/train_metrics.json` | 0.7715 es la validación del **v1**; la de B2 es 0.7560 (verificada) |
| d | Capítulo 8 | tres tablas con la nota «Datos no disponibles» | Jaccard LIME–SHAP nulo y pesos globales LIME no exportados: el capítulo no tiene contenido |

Sobre (d): el capítulo de interpretabilidad ocupa página y media y las tres tablas están
vacías. Conviene reducirlo a una nota metodológica de un párrafo en limitaciones.

---

## 4. Errores encontrados en el informe de Julio

Son de otra naturaleza. No son de transcripción: afectan a la validez de lo medido.

### 4.1 Contaminación del conjunto de prueba — **crítico, invalida el resultado**

Es el hallazgo central de esta auditoría. La cadena está documentada en su propio
`estadisticas3.ipynb`:

1. **Celda 5.** Evalúa el modelo baseline sobre `test.csv` y aísla los falsos positivos.
2. **Celda 7.** Los exporta a `falsos_positivos_diagnostico.csv` — 28 textos, **los 28 del test**.
3. **Celda 8.** Construye `train_mitigado.csv` reinyectando esos textos con `label = 0` más
   variantes con la jerga sustituida.
4. **Celda 24.** Reentrena el modelo sobre `train_mitigado.csv`.
5. **Celdas 25–28.** Mide el FPR sobre `test.csv` y reporta que bajó.

Verificación aritmética:

```
falsos_positivos_diagnostico.csv : 28 filas
  ∩ test.csv  = 28        <- el 100 %
  ∩ val.csv   = 0
  ∩ train.csv = 0

train_mitigado.csv : 2165 filas (train v1 = 2144, añadidas = 21)
  filas presentes literalmente en test.csv = 21
```

**21 textos del conjunto de prueba están en su conjunto de entrenamiento, etiquetados como
No Tóxico, y son exactamente los textos sobre los que después mide la mejora del FPR.** El
modelo no aprendió a no equivocarse: memorizó las respuestas de los casos en los que se
equivocaba. Cualquier cifra de FPR del `modelo_mitigado` sobre `test.csv` está inflada por
construcción, y con ella el 14.63 %.

### 4.2 La comparación 44.83 % → 14.63 % mide dos cosas distintas — **crítico**

Reproduje los dos números y los dos son correctos por separado. El problema es que no son la
misma métrica:

| | Qué es | Población | n | Modelo |
|---|---|---|---|---|
| 44.83 % | FPR de No Tóxico **con jerga** | subconjunto con `n_jerga > 0` | 29 | `xlmr_v1` |
| 14.63 % | FPR binario **sobre todos** los No Tóxico | todos los negativos del test | 123 | `xlmr_mit` |

La figura 2 del informe los pone como dos barras del mismo gráfico bajo el rótulo «FPR en
frases con jerga regional». Comparadas sobre la misma población y sobre el mismo test, las
cifras reales son:

| | FPR jerga (n = 29) | FPR sin jerga (n = 94) | FPR binario (n = 123) |
|---|---|---|---|
| `xlmr_v1` (baseline) | 0.4483 | 0.1596 | 0.2276 |
| `xlmr_mit` (mitigado) | **0.3103** | 0.0957 | 0.1463 |

La mejora real en jerga es de 44.83 % a **31.03 %**, no a 14.63 %. Y esos 13.8 puntos siguen
contaminados por lo de 4.1.

### 4.3 El conjunto «N = 1050» no existe — **crítico**

El informe declara los resultados «en el conjunto de validación dialectal salvadoreño
(N = 1050)». Las particiones del proyecto son 2,144 / 3,293 (train), 459 (val) y 460 (test).
No hay ningún conjunto de 1,050, no está entregado y no se documenta cómo se construiría.

Además **sus propias salidas lo contradicen**: el `classification_report` de la celda 28, que
es de donde salen las tres cifras publicadas, imprime soporte 123 / 159 / 95 / 83 y total
**460**. Las métricas son del test del proyecto, no de un conjunto de 1,050.

Es la reincidencia de un patrón: en el informe de agosto la figura 1 rotulaba el conjunto de
evaluación como «N = 3063» (el corpus completo) cuando la tabla de al lado decía n = 460.

### 4.4 No reporta F1-macro, que es la métrica del proyecto — **crítico**

El informe da accuracy y dos recalls sueltos. No aparece el F1-macro en ninguna página. Su
propio notebook **sí lo calcula**: la celda 28 imprime `macro avg … 0.8009`. Se omitió del
informe.

Calculado sobre los pesos entregados y el test real:

| Configuración | F1-macro | Accuracy |
|---|---|---|
| `xlmr_v1` (baseline de agosto) | **0.8058** | 0.8065 |
| `xlmr_mit`, nivel 1 (argmax) | **0.7887** | 0.7891 |
| `xlmr_mit`, nivel 2 (+ umbrales) | 0.7876 | 0.7870 |
| `xlmr_mit`, nivel 3 (+ regex) | **0.7837** | 0.7826 |

**El Prototipo V2 es peor que el modelo de agosto en la métrica principal**, y cada capa de
mitigación lo empeora un poco más. La caída total es de 0.0221. Esto no se deduce de ningún
número del informe porque el informe no publica la métrica en la que ocurre.

### 4.5 El filtro regex no hace lo que dice — **alto**

Medido sobre `test.csv`: el filtro se activa en **2 textos de 460**, y el FPR es **idéntico**
antes y después (0.1463 en los tres niveles). La reducción del FPR que el informe atribuye al
pipeline de mitigación viene enteramente del reentrenamiento contaminado. Las capas 2, 3 y 4
no aportan nada positivo y restan 0.005 de F1-macro.

### 4.6 Prueba de evadibilidad — **alto**

Pedida explícitamente. Tomé 100 casos de amenaza (11 del grupo C, 6 del grupo G y las 83
amenazas reales de `test.csv`), les antepuse cada uno de los seis marcadores afectivos del
filtro y los pasé por el pipeline completo.

| Prefijo | Amenazas clasificadas como No Tóxico | Δ vs. sin prefijo |
|---|---|---|
| *(ninguno)* | 1 / 100 | — |
| `mi hermano, ` | **21 / 100** | +20 |
| `gracias, ` | **20 / 100** | +19 |
| `te quiero pero ` | **20 / 100** | +19 |
| `qué onda, ` | 19 / 100 | +18 |
| `todo bien, ` | 17 / 100 | +16 |
| `buena onda, ` | 17 / 100 | +16 |

**Una de cada cinco amenazas se neutraliza anteponiendo una palabra.** Ejemplos reales de la
salida:

```
gracias, Te voy a dar piso                            -> No Tóxico
gracias, Ya sabés lo que te espera :ataúd:            -> No Tóxico
gracias, Te voy a buscar mañana :cuchillo_de_cocina:  -> No Tóxico
gracias, Aquí los linchamos                           -> No Tóxico
gracias, Otro malparido menos                         -> No Tóxico
```

El mecanismo es de dos pasos: el prefijo afectivo empuja la predicción de Amenazas a
Ofensivo, y entonces el filtro —que solo actúa sobre Ofensivo— la manda a No Tóxico. Sin el
filtro serían 8 de 100; con él, 20. **La capa de mitigación multiplica por 2.5 la
evadibilidad del sistema.**

El informe reconoce el problema en su sección 4.2 con el ejemplo «Gracias por arruinarme el
día, cerote», y aun así propone el pipeline como solución de producción.

### 4.7 Errores menores y observaciones

| # | Qué | Detalle |
|---|---|---|
| a | Cifras del baseline arrastradas | 81.09 % y 77.38 % vienen del informe de agosto, ya señalados como incorrectos el 1 de septiembre. Los verificados son 80.65 % y 78.31 % |
| b | Baseline internamente inconsistente | La tabla por clase de agosto promedia 0.8054, no el 0.8100 declarado. Su matriz de confusión suma 371 aciertos, o sea 0.8065, no 0.8109 |
| c | El informe lista 5 patrones regex | El `config_umbrales.json` tiene **6**: falta `\bbuena onda\b` |
| d | Ajuste y evaluación sobre el mismo conjunto | Dice que los umbrales se optimizaron «sobre validación» y reporta «en el conjunto de validación dialectal». Las celdas 21–28 son una búsqueda manual de umbrales **sobre el test**, iterada hasta que los dos recalls superaron el 80 % |
| e | Regla de decisión mal documentada | El informe presenta los umbrales como una tabla sin orden. En el código es una cascada AV → DO → LO → NT, y el 0.00 de No Tóxico nunca se evalúa: es el `else` final. El informe no lo dice |
| f | `inferencia.py` no implementa el pipeline | Lo único ejecutable que entregó hace `argmax` puro: sin umbrales, sin regex. El pipeline de cuatro niveles solo existe dentro de los notebooks |
| g | `v_2/` duplica `modelo_mitigado/` | Byte a byte (md5 `8f87e8a7…`). 1.1 GB repetidos en la entrega |
| h | Falta trazabilidad | No hay `training_args.bin`, `train_metrics.json`, `test_metrics.json` ni manifiesto. Cristian sí los entrega |
| i | `id2label` | **Corregido.** Trae los cuatro nombres reales. El pendiente de agosto queda cerrado |
| j | Registro impreciso | «en producción», «desplegada», «Sistema Mitigado v1.4». No hay nada desplegado |

---

## 5. Rendimiento verificado de los cuatro modelos

Todo lo que sigue son mediciones propias sobre `test.csv` (n = 460).

### 5.1 Globales

| | mBERT v1 | mBERT B2 | XLM-R v1 | XLM-R mit. |
|---|---|---|---|---|
| **F1-macro** | 0.7777 | 0.7610 | **0.8058** | 0.7887 |
| Accuracy | 0.7826 | 0.7674 | **0.8065** | 0.7891 |
| Aciertos | 360/460 | 353/460 | **371/460** | 363/460 |
| ECE | 0.1570 | 0.1640 | **0.0871** | 0.0970 |
| Log-loss | 0.8721 | 0.8328 | **0.6350** | 0.6635 |
| IC 95 % bootstrap | [0.7363, 0.8144] | [0.7172, 0.7983] | [0.7665, 0.8420] | [0.7486, 0.8257] |

Ninguno alcanza la meta de 0.80 con holgura. XLM-R v1 la roza en el punto estimado (0.8058)
pero el extremo inferior del intervalo está en 0.7665: **no se puede afirmar que el proyecto
cumple la meta**. Hay que escribirlo así.

### 5.2 Por clase (F1)

| Clase | Soporte | mBERT v1 | mBERT B2 | XLM-R v1 | XLM-R mit. |
|---|---|---|---|---|---|
| No Tóxico | 123 | 0.8136 | 0.7837 | 0.8155 | **0.8502** |
| Lenguaje Ofensivo | 159 | 0.7951 | 0.7925 | **0.8061** | 0.7677 |
| Discurso de Odio | 95 | 0.7461 | 0.7330 | **0.8041** | 0.7415 |
| Amenazas/Violencia | 83 | 0.7561 | 0.7349 | **0.7975** | 0.7953 |

### 5.3 Matrices de confusión (fila = real, columna = predicho)

```
mBERT B2                      XLM-R v1                      XLM-R mitigado
      NT   LO   DO   AV             NT   LO   DO   AV             NT   LO   DO   AV
NT    96   16    6    5       NT    95   16    7    5       NT   105    6    8    4
LO    11  126   13    9       LO     9  133    8    9       LO    10  114   23   12
DO    10    7   70    8       DO     5   11   78    1       DO     8    7   76    4
AV     5   10    7   61       AV     1   11    6   65       AV     1   11    3   68
```

El mitigado de Julio gana 10 aciertos en No Tóxico (105 vs 95) y pierde 19 en Ofensivo
(114 vs 133), la mayoría a Discurso de Odio. Es el efecto esperado de subir el recall de Odio
bajando su umbral a 0.36: se compra recall en Odio con precisión en Ofensivo.

### 5.4 Sonda dirigida de ofuscación y emojis — 204 casos nuevos

Construí una sonda aparte, hoy, con 204 casos que **ningún modelo pudo haber visto ni en
entrenamiento ni en la batería de 144**. Cubre lo que pediste: groserías disfrazadas con `*`,
`@`, `#`, sustitución de vocales por dígitos, amenazas de muerte literales y ofuscadas,
eufemismos salvadoreños, y emojis. Con el normalizador del contrato aplicado.

| Familia | n | mBERT v1 | mBERT B2 | XLM-R v1 | XLM-R mit. |
|---|---|---|---|---|---|
| 1. Ofuscación de groserías | 66 | 52 | 45 | **59** | 37 |
| 2. Amenazas de muerte | 72 | 23 | **61** | 26 | 39 |
| 3. Emoji de amenaza (🔫🔪⚰️💀🪦💣) | 12 | 0 | **12** | 0 | 0 |
| 4. Emoji de odio (🐒🧼🐷🐋) | 4 | 2 | **4** | **4** | **4** |
| 5. Emoji inofensivo (❤️😂🎉🙏) | 16 | 3 | **16** | 5 | 8 |
| 6. Par mínimo de emoji | 14 | 4 | **14** | 2 | 2 |
| 7. Jerga salvadoreña inofensiva | 10 | 2 | **8** | 2 | 3 |
| 8. Control en español estándar | 10 | 6 | **7** | **7** | 8 |
| **GLOBAL** | **204** | 92 | **167** | 105 | 101 |

**mBERT B2 gana por 62 puntos sobre el segundo.** Y gana justo donde importa para moderación:

- **Amenazas ofuscadas:** 61/72 contra 23/72 del v1. La versión v1 clasificaba «Te voy a
  m4t4r» como Ofensivo; B2 la clasifica como Amenaza. Los cuatro modelos aciertan la forma
  literal; solo B2 aguanta el disfraz.
- **Emojis de amenaza:** 12/12 contra **0/12 de los otros tres**. Ni XLM-R v1 ni el mitigado
  de Julio reconocen «Te espero en la esquina 🔫» como amenaza: los dos dicen Ofensivo o
  No Tóxico.
- **Emoji inofensivo:** 16/16. Los demás siguen disparando toxicidad ante un ❤️ o un 🎉 en
  texto amable — el atajo «hay emoji, es ofensivo» que motivó B2 sigue vivo en los otros tres.

Tasa de fuga por tipo de disfraz, sobre las familias 1 y 2 (porcentaje de casos en que el
disfraz hace caer la predicción por debajo de la clase esperada; más bajo es mejor):

| Disfraz | Ejemplo | mBERT v1 | mBERT B2 | XLM-R v1 | XLM-R mit. |
|---|---|---|---|---|---|
| asterisco | `p**a` | 66.7 % | **16.7 %** | 41.7 % | 33.3 % |
| arroba | `put@` | 41.7 % | **0.0 %** | 33.3 % | 25.0 % |
| numeral | `pend#j#` | 50.0 % | 33.3 % | **16.7 %** | 25.0 % |
| leet vocales | `m4t4r`, `m13rda` | 41.7 % | **8.3 %** | 41.7 % | 16.7 % |
| leet consonantes | `pu7a`, `mier6a` | 50.0 % | **8.3 %** | 33.3 % | 16.7 % |
| espaciado | `p u t a` | 58.3 % | **8.3 %** | 41.7 % | **8.3 %** |
| punto | `p.u.t.a` | 50.0 % | **16.7 %** | 41.7 % | 33.3 % |
| eufemismo | «dar piso», «dar cuello» | 50.0 % | **33.3 %** | 66.7 % | 50.0 % |

El disfraz más eficaz contra todos los modelos sigue siendo el **eufemismo salvadoreño**: «te
voy a dar piso», «lo van a poner a dormir». No es ofuscación ortográfica, es conocimiento
cultural, y ahí ni siquiera B2 pasa de dos tercios.

Brecha dialectal en la sonda (familia 7 jerga contra familia 8 su equivalente estándar):

| | FPR jerga | FPR control | Brecha |
|---|---|---|---|
| mBERT v1 | 0.80 | 0.40 | **+0.40** |
| **mBERT B2** | **0.20** | 0.30 | **−0.10** |
| XLM-R v1 | 0.80 | 0.30 | **+0.50** |
| XLM-R mitigado | 0.70 | 0.20 | **+0.50** |

Sobre casos nuevos, B2 es el único que no penaliza la jerga; de hecho la brecha se invierte.
El pipeline de Julio deja la brecha exactamente donde estaba en el v1.

### 5.5 Un apunte sobre el normalizador — responsabilidad mía

Al correr la sonda con emoji crudo y con emoji normalizado salió una diferencia grande:

| | Emoji crudo | Normalizado | Δ |
|---|---|---|---|
| mBERT B2 | 31/46 | **46/46** | +15 |
| XLM-R v1 | 24/46 | 11/46 | −13 |
| XLM-R mit. | 24/46 | 14/46 | −10 |

Dos cosas. La primera: **si la API no aplica `normalize_for_model`, mBERT B2 pierde un tercio
de su ventaja en emojis**. La demojización no es cosmética, es parte del modelo. Hay que
blindarlo en el endpoint.

La segunda es un defecto del léxico que mantengo yo: la librería `emoji` traduce 🔫 como
`:pistola_de_agua:`, no como `:pistola:`. Los modelos aprenden sobre «pistola de agua». No ha
impedido que B2 acierte los 12 casos, pero es un mapeo semánticamente equivocado en un emoji
que el proyecto documenta como vehículo de amenaza. Corregir el mapeo en
`src/features/normalization.py` y reentrenar.

### 5.6 Comparación pareada de los cuatro

McNemar exacto, mismas 460 instancias:

| A | B | b (solo A) | c (solo B) | p | Favorece |
|---|---|---|---|---|---|
| mBERT v1 | mBERT B2 | 24 | 17 | 0.3489 | v1, n.s. |
| mBERT v1 | XLM-R v1 | 25 | 36 | 0.2000 | XLM-R, n.s. |
| **mBERT B2** | **XLM-R v1** | **26** | **44** | **0.0414** | **XLM-R, significativo** |
| XLM-R v1 | XLM-R mit. | 37 | 29 | 0.3891 | v1, n.s. |
| mBERT B2 | XLM-R mit. | 33 | 43 | 0.3019 | mitigado, n.s. |

Solo una comparación de seis es significativa, y es la que contradice la conclusión 3 de
Cristian.

---

## 6. Juicio metodológico

### 6.1 ¿Cuánto de la mejora de B2 es memorización de plantillas?

Es la pregunta legítima y la respuesta es: una parte, no toda.

| Evidencia | Independencia de las plantillas | Mejora B2 vs v1 |
|---|---|---|
| Grupos D + E de la batería | baja — plantillas emparentadas | 2/14 → 13/14 |
| `test.csv` real, sonda de jerga | total | 0.4138 → **0.4138** (nada) |
| Grupo F, falsos amigos | alta | 17/34 → 30/34 |
| **Sonda dirigida de hoy** | **total** | 92/204 → **167/204** |

Los grupos D y E están inflados: ahí el modelo reconoce plantillas. El test real no muestra
mejora. Pero el grupo F y sobre todo la sonda nueva, escrita después de que el modelo se
entrenara y sin reutilizar ninguna plantilla del generador, muestran una mejora grande y real.

Mi lectura: **la mejora de representación existe y es sustancial en robustez, pero la sonda
de jerga del test real es demasiado pequeña (n = 29) para detectarla.** Doce falsos positivos
de veintinueve; un solo caso mueve la métrica 3.4 puntos. No se puede concluir ni que mejoró
ni que no mejoró en datos reales con ese tamaño. Lo honesto en la tesina es declarar el
tamaño y decir que el corte no tiene potencia estadística.

### 6.2 Solape entre la batería y el entrenamiento — sigue sin corregirse

Hay **7 textos** de la batería adversarial que aparecen literalmente en el train de B2:

```
te voy a matar              te voy a m4t4r             te voy a m*tar
te voy a dar piso           te espero afuera :cuchillo_de_cocina:
te espero afuera :pistola_de_agua:
ese cerote es mi mejor amigo desde la escuela
```

Son las mismas 7 que se detectaron en agosto. Cuatro están en el grupo C, que es justo el
grupo donde B2 saca 11/11. **La batería de 144 no es un conjunto limpio de generalización** y
hay que declararlo cuando se reporte el 120/144. Es responsabilidad mía corregirlo: o se
quitan esas 7 filas de la batería, o se quitan del train.

### 6.3 ¿Son comparables los dos enfoques?

No, y conviene decir por qué en lugar de ponerlos en la misma tabla.

| | Cristian | Julio |
|---|---|---|
| Qué cambió | los datos de entrenamiento | reglas sobre la salida |
| Dónde vive la mejora | en la representación del modelo | en una capa externa |
| ¿Reproducible? | sí, 26/26 cifras | no, 3/11 |
| ¿Contaminado? | no, hashes verificados | sí, 21 textos del test |
| ¿Evadible? | como cualquier clasificador | sí, con una palabra |
| Costo en F1-macro | −0.0167 declarado | −0.0221 no declarado |
| ¿Mejora la métrica del proyecto? | no, y lo dice | no, y no lo dice |

El de Cristian es un experimento de aprendizaje automático. El de Julio es ingeniería de
reglas, que sería una contribución perfectamente legítima si estuviera medida sobre un
conjunto limpio y comparada con la métrica del proyecto. No lo está.

---

## 7. Correcciones pendientes

### Cristian

| # | Tarea | Severidad |
|---|---|---|
| 1 | Corregir el hallazgo 3: McNemar favorece a **XLM-R**, no a mBERT B2. Declarar que B2 pierde el empate estadístico | Crítica |
| 2 | Rehacer la tabla de familias con **una sola batería**, la entregada. Hoy compara mBERT en su batería contra XLM-R en la oficial | Crítica |
| 3 | Resolver la contradicción entre los hallazgos 2 y 5: la mejora dialectal se observa en la batería y **no** en el test real; declarar además que n = 29 no da potencia | Crítica |
| 4 | Corregir la celda F de XLM-R: 20/34 en la batería entregada, no 26/34 | Alta |
| 5 | Etiquetar la magnitud de cada columna de la tabla de familias (aciertos vs. falsos positivos) | Alta |
| 6 | Actualizar el texto de los baselines TF-IDF a 0.7482 / 0.7354 / 0.6932 | Media |
| 7 | Corregir la columna de checkpoint (1644) y la fila de 0.7715 en la tabla de trazabilidad | Media |
| 8 | Retirar el capítulo de interpretabilidad o reducirlo a una nota en limitaciones | Media |

### Julio

| # | Tarea | Severidad |
|---|---|---|
| 1 | **Reentrenar desde cero sin los 21 textos del test.** El `modelo_mitigado` actual no es utilizable: sus métricas sobre `test.csv` están contaminadas | Crítica |
| 2 | Reportar **F1-macro** sobre `test.csv`, con y sin pipeline. Su propio notebook ya lo calcula | Crítica |
| 3 | Retirar «N = 1050». Las cifras son sobre n = 460 según su propio `classification_report` | Crítica |
| 4 | Rehacer la comparación de FPR sobre la **misma población**: jerga contra jerga (44.83 % → 31.03 %), no jerga contra todos | Crítica |
| 5 | Separar el conjunto de ajuste de umbrales del de evaluación. Las celdas 21–28 iteran umbrales sobre el test | Crítica |
| 6 | Retirar el filtro regex o documentarlo como vulnerabilidad: multiplica por 2.5 la evadibilidad y no mejora el FPR | Alta |
| 7 | Corregir el baseline: accuracy 0.8065 y recall Amenazas 0.7831 | Alta |
| 8 | Especificar la regla de decisión: cascada AV → DO → LO → NT; el 0.00 es el `else`, no un umbral | Alta |
| 9 | Documentar los **6** patrones regex, no 5 | Media |
| 10 | Reentrenar con `data/dataset_b2/` y los pesos `[0.9198, 0.9376, 0.9720, 1.2233]`. Sigue usando el train v1 | Media |
| 11 | Hacer que `inferencia.py` implemente el pipeline que describe el informe | Media |
| 12 | Entregar trazabilidad: `training_args`, métricas en JSON, manifiesto de hashes | Media |
| 13 | Borrar `v_2/`, duplicado exacto de `modelo_mitigado/` | Baja |
| 14 | Reencuadrar «producción / desplegado» como prototipo experimental | Baja |

### Willian (mías)

| # | Tarea | Severidad |
|---|---|---|
| 1 | Quitar las 7 filas solapadas entre la batería adversarial y el train de B2 | Alta |
| 2 | Corregir el mapeo 🔫 → `:pistola_de_agua:` en `normalization.py` | Alta |
| 3 | Ampliar la sonda dialectal del test: n = 29 no da potencia para medir el sesgo | Alta |
| 4 | Incorporar la sonda de 204 casos al conjunto diagnóstico permanente | Media |
| 5 | Recolectar emojis de amenaza reales: la cobertura sigue siendo 100 % sintética | Media |

---

## 8. Recomendación para la tesina

### Qué modelo reportar

**Reportar los dos, con papeles distintos, y no declarar cumplida la meta de 0.80.**

1. **XLM-R v1 es el mejor clasificador del proyecto en la métrica principal.** F1-macro
   0.8058, la mejor calibración (ECE 0.0871, menos de la mitad que mBERT) y el mejor
   desempeño en las dos clases críticas. Es la cifra de titular.

2. **Pero es frágil.** 0/12 en emojis de amenaza, 26/72 en amenazas ofuscadas, brecha
   dialectal de +0.50. Un F1 alto sobre un test que no contiene ofuscación no dice nada sobre
   cómo se comporta ante evasión deliberada, que es exactamente lo que hay en moderación real.

3. **mBERT B2 es el modelo robusto.** 167/204 en la sonda nueva contra 105 de XLM-R v1,
   12/12 en emojis de amenaza, cero falsos negativos en amenazas ofuscadas, brecha dialectal
   invertida. Paga 0.0448 de F1-macro por ello.

El resultado defendible del proyecto es precisamente esa tensión, y es un resultado
interesante: **el aumento sintético dirigido compra robustez ante evasión al precio de F1
sobre la distribución natural.** Está cuantificado en las dos direcciones y es reproducible.
Vale más que un F1 alto sin análisis de robustez.

### Qué cifras van al documento

| Bloque | Cifra | Fuente |
|---|---|---|
| Métrica principal | XLM-R v1 **0.8058** IC95 [0.7665, 0.8420] · mBERT B2 **0.7610** IC95 [0.7172, 0.7983] | reejecución propia |
| Meta 0.80 | **No alcanzada con significancia.** El IC de XLM-R incluye valores por debajo de 0.77 | — |
| Comparativa | McNemar b = 26, c = 44, p = 0.0414, **a favor de XLM-R** | reejecución propia |
| Robustez | Batería 144 (declarando el solape de 7) + sonda de 204 casos | reejecución propia |
| Fairness | FPR jerga 0.4138 / sin jerga 0.1596, **declarando n = 29** | reejecución propia |
| Pisos triviales | mayoritaria 0.1284 · azar 0.2451–0.2496 | reejecución propia |
| Baselines | LinearSVC 0.7482 · LogReg 0.7354 · MNB 0.6932 | reejecución propia |

### Qué no va

- **Ninguna cifra del Prototipo V2 en su forma actual.** No por rigor excesivo: por
  contaminación del test. Las tres cifras de resultado no se reproducen desde los pesos
  entregados y el modelo vio 21 textos del conjunto de prueba.
- **El 14.63 % de FPR.** Compara poblaciones distintas y está contaminado.
- **El conjunto N = 1050.** No existe.
- **El 120/144 sin declarar** que 7 de esos 144 están en el train y que la tabla mezcla dos
  baterías.
- **El capítulo de interpretabilidad** mientras las tres tablas digan «datos no disponibles».

### Dónde encaja el trabajo de Julio

Como sección de **alternativas evaluadas y descartadas**, que es un aporte real si se presenta
así. Su sección 4, el análisis crítico de las limitaciones de las heurísticas, está bien
escrita y es honesta: anticipa el fallo de «gracias» antes de que nadie lo midiera. Esa
sección más la medición de evadibilidad de 7.4.6 componen un argumento sólido a favor de
resolver el sesgo con datos y no con reglas — que es justamente lo que la comparación con B2
demuestra. Presentado así, su trabajo sostiene la conclusión del capítulo en lugar de
competir con ella.

---

## Anexo. Artefactos generados

Todo en `reports/v2_auditoria/`:

| Fichero | Contenido |
|---|---|
| `manifiesto_pesos.json` | SHA-256, arquitectura e `id2label` de los cuatro checkpoints |
| `logits_<modelo>_<conjunto>.npy` | Logits crudos: 4 modelos × {test, val, adv, sonda} |
| `metricas_reproducidas.json` | Métricas globales, por clase, matrices, cortes e IC |
| `mcnemar.json` | Las seis comparaciones pareadas y los Δ F1 con IC bootstrap |
| `preds_<modelo>.csv` | `ID,y_pred` sobre test, para comparación pareada |
| `bateria_predicciones.csv` | Batería entregada, 144 casos, predicción de cada modelo |
| `bateria_cristian_predicciones.csv` | Batería propia de Cristian, para el contraste de 3.2 |
| `sonda_predicciones.csv` | Sonda dirigida, 204 casos, crudo y normalizado |
| `evadibilidad_julio.csv` | 700 filas: 100 amenazas × 7 prefijos, salida de los tres niveles |
| `pdf/*.txt` | Texto extraído de los cinco PDF auditados |

Scripts en `src/audit/`: `reproducir_2v.py`, `metricas_2v.py`, `bateria_2v.py`,
`pipeline_julio.py`, `sonda_ofuscacion_emoji.py`. Todos deterministas con semilla 42.
