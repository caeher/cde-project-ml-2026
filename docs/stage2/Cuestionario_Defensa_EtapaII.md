# Cuestionario de defensa — Etapa II

**Para:** Willian Alexander Chávez Servellón
**Uso:** 15 minutos de preguntas tras la exposición

Las respuestas están redactadas para decirse en voz alta, no para leerse. Cada una arranca con la frase directa y después el respaldo — si te interrumpen a la mitad, lo importante ya se dijo.

---

## Cómo usar esto

Las preguntas están ordenadas por probabilidad de que caigan, no por tema. Las **marcadas con ⚠ son las peligrosas**: apuntan a una debilidad real o a una inconsistencia del reporte. Esas son las que hay que tener memorizadas, no leídas.

**Tres reglas:**

1. Si no lo medimos, se dice «eso no lo medimos» y se ofrece cómo se mediría. Nunca se estima en voz alta.
2. Si la pregunta señala un error real, se reconoce en la primera frase. Discutirlo cuesta más credibilidad que el error mismo.
3. Ninguna respuesta debería pasar de noventa segundos. Si el jurado quiere más, pregunta de nuevo.

---

# A. Sobre el resultado y la estadística

### A1 ⚠ — ¿El modelo individual también alcanzó la meta?

**No.** Su intervalo va de 0.7912 a 0.8610, o sea que cruza la meta: ni la supera ni la descarta con este tamaño de prueba. El único sistema que la supera con el intervalo completo es el ensemble, con extremo inferior en 0.8191. Por eso el sistema que proponemos es el ensemble y no el modelo individual.

> *Si insisten:* En el reporte hay una frase en la sección 12.2 que dice que ambos extremos están por encima de 0.80. Es un error de redacción de nuestra parte; la Tabla 13 tiene el valor correcto, 0.7912, y la conclusión válida es la que acabo de dar.

*(Reconocerlo de frente cuesta mucho menos que defender lo indefendible. El número 0.7912 está impreso.)*

---

### A2 ⚠ — Dicen que las tres comparaciones de McNemar fueron significativas, pero los p-valores no lo son.

Tiene razón y es un error de redacción del reporte. Los valores de la Tabla 15 son los correctos: frente a mBERT B2 la diferencia **sí** es significativa, con p igual a 0.0026. Frente al XLM-R mitigado, p es 0.0567, marginal, no significativa a alfa 0.05. Y frente a XLM-R v1, p es 0.2820: **no concluyente**.

La lectura correcta es que la mejora del modelo de esta etapa es estadísticamente sólida frente a dos de los cuatro sistemas anteriores, y frente al mejor de ellos el test no tiene potencia suficiente para separarlos. Es coherente con lo que ya dijimos sobre el tamaño del conjunto de prueba.

---

### A3 — ¿Por qué reportan intervalos de confianza y no solo el F1?

Porque con cuatrocientos sesenta instancias la estimación puntual no distingue una mejora real de la variación del muestreo.

Lo medimos de dos formas. La dispersión entre semillas del mismo modelo fue de 1.8 puntos de F1-macro. Y el rango entre los cinco pliegues de la validación cruzada fue de 0.8128 a 0.8560, casi cuatro puntos y medio. Es decir, dos números que difieren en dos o tres puntos pueden ser el mismo sistema.

De hecho ese fue el hallazgo que nos hizo revisar la Etapa I: varias mejoras que se habían reportado allí eran del mismo orden de magnitud que ese ruido.

---

### A4 — ¿Cuántas veces consultaron el conjunto de prueba?

Una vez, con los modelos ya seleccionados.

La optimización de hiperparámetros se hizo sobre validación. La selección de semilla y la regla del ensemble se fijaron sobre validación y antes de mirar prueba. La validación cruzada se hizo sobre entrenamiento y validación unidos, reservando prueba.

Y verificamos la integridad: el SHA-256 de test.csv coincide con el de la Etapa I, así que no se modificó ni una fila entre etapas.

---

### A5 — ¿Por qué el ensemble de tres semillas si sobre validación había combinaciones mejores?

Es correcto: sobre validación, el par de semillas 42 y 2026 daba 0.8521 y la mejor semilla sola daba 0.8555, mientras que el promedio de las tres daba 0.8416.

Elegimos el promedio de las tres porque **la regla se fijó antes de ver prueba**, y cualquier criterio de selección —incluso sobre validación— reintroduce el sesgo de quedarse con la combinación afortunada. Con tres semillas, el promedio completo era la opción menos sobreajustada.

Hubo además una razón concreta: la semilla 2026, que era la mejor sobre validación, conservaba cuatro falsos positivos en la sonda de construcción. Elegirla habría sido seleccionar justamente por la métrica que no veía el defecto. Y sobre prueba la decisión se validó: el ensemble dio 0.8529 y el individual 0.8268.

---

### A6 — ¿No es sobreajuste haber optimizado veinte configuraciones?

La optimización se hizo íntegramente sobre validación, cuatrocientos cincuenta y nueve instancias que no son el conjunto de prueba. El riesgo de sobreajustar a validación existe y es real.

Lo controlamos de dos maneras. Primero, la validación cruzada de cinco pliegues, que no usa la partición de validación y da 0.8274 ± 0.0170, consistente con el resultado de prueba. Segundo, el intervalo de confianza sobre prueba, que es una medición independiente.

Si hubiéramos sobreajustado a validación, esperaríamos ver el resultado de prueba claramente por debajo. No ocurrió.

---

### A7 — ¿Por qué F1-macro y no accuracy?

Porque el corpus está desbalanceado y las clases no valen lo mismo.

Amenazas y Violencia es la clase minoritaria, con ochenta y tres casos en prueba, y es la que más importa detectar. Un modelo que acertara solo la clase mayoritaria tendría una accuracy aceptable y un F1-macro de 0.1284, que es el piso trivial que reportamos. El F1-macro trata las cuatro clases por igual y penaliza exactamente ese comportamiento.

---

# B. Sobre los datos

### B1 ⚠ — El 73 % de su corpus de entrenamiento es sintético. ¿Eso no invalida el resultado?

Es la objeción más razonable que se le puede hacer al trabajo, y la contestamos con tres mediciones.

Primero: **los sintéticos están solo en entrenamiento.** Validación y prueba son cien por ciento reales y no se tocaron entre etapas; verificamos sus SHA-256. Nada de lo que reportamos se mide sobre texto de plantilla.

Segundo: en la validación cruzada los sintéticos se asignaron siempre al lado de entrenamiento y **cada pliegue se evaluó exclusivamente sobre publicaciones reales**, dos mil seiscientas tres en total. El resultado, 0.8274, es consistente con el de prueba.

Tercero, y es el más importante: el proceso de optimización **decidió por sí solo** que los sintéticos debían pesar 0.75 y no 1.0. No se lo impusimos.

Dicho esto, la limitación es real y está declarada: el corpus real sigue siendo de 2,144 publicaciones y esa es la restricción de fondo del trabajo.

---

### B2 ⚠ — ¿Cómo saben que el modelo no está memorizando las plantillas?

En parte lo estaba, y lo encontramos nosotros. Es el hallazgo de la diapositiva once.

El modelo había aprendido la construcción «te voy a» en lugar del significado de los verbos, porque el generador solo la rellenaba con verbos de agresión. Clasificaba «voy a comer» como amenaza con 82.6 % de confianza.

Dos cosas sobre eso. La primera es que **el F1-macro no lo detectaba**: las construcciones afectadas eran el tres por ciento del conjunto de prueba, así que el atajo podía estar completamente instalado sin costar casi nada de métrica. La segunda es que lo corregimos añadiendo contraejemplos con los mismos portadores y verbos inocuos, y la probabilidad media de amenaza en frases inocuas cayó del 53 % al 1.6 % sin perder ninguna amenaza real.

De ahí salió la regla de diseño que incorporamos al generador: toda estructura usada para producir una clase debe aparecer también, con relleno distinto, produciendo otra.

---

### B3 — ¿De dónde salieron las publicaciones reales y cómo las etiquetaron?

Son 2,144 publicaciones recolectadas de X y Facebook en contexto salvadoreño, etiquetadas en las cuatro clases de la taxonomía con una guía de anotación común.

El dato relevante para juzgar el trabajo es el acuerdo entre anotadores: 0.8095 de F1-macro. Sobre los casos en que los anotadores discreparon, el mejor modelo de la etapa anterior acertaba prácticamente al azar. Por eso decimos que la calidad de la etiqueta es el techo real del problema: el modelo no puede ser más consistente que sus etiquetas.

---

### B4 — ¿Verificaron que no hay fuga entre entrenamiento y prueba?

Sí, y encontramos fuga.

Verificamos que ningún texto de entrenamiento apareciera en validación, en prueba o en la batería adversarial. La comprobación detectó siete filas que el proyecto arrastraba desde agosto, compartidas entre la batería adversarial y el entrenamiento, y quedaron fuera.

Un detalle metodológico: la verificación se hizo también contra la normalización vigente del texto crudo, no solo contra la columna almacenada. Una de esas siete filas era invisible a la comparación directa porque la batería guardaba su texto normalizado con una versión anterior del normalizador.

---

### B5 — ¿Por qué no recolectaron más datos reales en lugar de generar sintéticos?

Es lo que deberíamos hacer y es la conclusión con la que cerramos: el siguiente salto son más datos reales y mejores etiquetas, no más arquitectura.

La restricción fue de tiempo y de capacidad de anotación. Anotar de forma consistente en cuatro niveles de gravedad con acuerdo entre anotadores es costoso, y no alcanzamos la meta de 771 ejemplos reales por clase ni en Discurso de Odio ni en Amenazas.

Los sintéticos fueron un paliativo dirigido a debilidades medidas, no un sustituto. Y medimos su límite: un subconjunto con 1,292 filas menos, que conservaba solo las familias dirigidas a una debilidad real, obtuvo 0.8472 frente a 0.8473 del conjunto completo. **La mitad de los sintéticos era prescindible.**

---

# C. Sobre el modelado

### C1 — ¿Por qué RoBERTuito y no un modelo más grande o más reciente?

Porque lo medimos y el tamaño no explicaba el resultado.

Comparamos siete arquitecturas con hiperparámetros idénticos sobre el mismo corpus. XLM-R large, con 560 millones de parámetros, obtuvo 0.8090 y tardó 42 minutos. RoBERTuito, con 109 millones, obtuvo 0.8272 en minuto y medio.

Lo que separó a los dos mejores fue el corpus de preentrenamiento: ambos habían sido preentrenados sobre publicaciones de redes sociales en español. La comparación limpia es TwitterXLM-R contra XLM-R base: misma arquitectura, mismo tamaño, mismo tokenizador, y 0.039 de diferencia atribuible únicamente al corpus de preentrenamiento.

Con 2,144 ejemplos reales, el cuello de botella no es la capacidad del modelo.

---

### C2 — ¿Probaron modelos generativos o LLMs?

No, y es una limitación del alcance que definimos.

El trabajo se acotó a modelos de codificador bidireccional con *fine-tuning*, por tres razones: el despliegue en hardware modesto —el modelo final se entrena en minuto y medio en una tarjeta de consumo—, la reproducibilidad determinista con semilla fija, y el costo.

Para un trabajo futuro sería una comparación válida, sobre todo en las figuras retóricas, que es donde el contexto amplio de un modelo generativo podría ayudar. Pero no lo medimos y no puedo afirmar nada al respecto.

---

### C3 — ¿Por qué mBERT y XLM-R quedaron tan abajo?

Por dos razones que medimos por separado.

La primera es el tokenizador. mBERT fue el peor del grupo: fertilidad de 1.805 subtokens por palabra frente a 1.470 de RoBERTuito, un 23 % más de fragmentación sobre el mismo texto. En mBERT «cerote» se parte en «cero» y «te», «maje» en «maj» y «e». El modelo nunca ve la palabra completa.

La segunda es el corpus de preentrenamiento: ambos fueron entrenados sobre texto general, principalmente enciclopédico, no sobre lenguaje de redes sociales.

Tengo que señalar que fueron los dos modelos que elegimos en la Etapa I, y que esa elección se hizo por convención y no por medición. Nos costó cerca de cuatro puntos de F1-macro.

---

### C4 — Extender el vocabulario con tokens del dialecto parecía una buena idea. ¿Por qué no funcionó?

La probamos en seis configuraciones y **perjudicó en las seis**.

La hipótesis era razonable: los marcadores de emoji se fragmentan en cuatro o más piezas, y añadir tokens de dominio debería ayudar. El problema es que un token nuevo nace con un vector aleatorio y no hay ejemplos suficientes para aprenderlo. Mientras tanto, sustituye una representación imperfecta pero informativa por ruido.

La documentamos como vía explorada y descartada. Nos pareció que tenía valor dejarla constando: es una idea que cualquiera que retome el trabajo va a considerar.

---

### C5 — ¿Los mismos datos sintéticos ayudaron a un modelo y perjudicaron al otro?

Sí, y es uno de los resultados más informativos de la ablación.

Con TwitterXLM-R, de 278 millones de parámetros, los sintéticos costaron hasta 2.5 puntos de F1. Con RoBERTuito, de 109 millones, aportaron hasta 2 puntos.

Nuestra lectura es que el modelo grande tenía capacidad de sobra para memorizar la estructura de las plantillas, y esa estructura no existe en el lenguaje real. El pequeño no podía memorizarla y se quedó con la señal. Es coherente con el hallazgo del atajo sintáctico.

---

# D. Sobre equidad, sesgos y ética

### D1 ⚠ — La reducción del sesgo dialectal está medida sobre 29 casos. ¿Eso sostiene la conclusión?

**No, y por eso no la presentamos como definitiva.**

Veintinueve casos significa que un solo ejemplo mueve la métrica 3.4 puntos. Lo declaramos en la diapositiva, en la sección de análisis de sesgos y en las limitaciones del reporte.

Lo que sí sostenemos es que la tendencia es consistente con el resto de las mediciones: la sonda dirigida, la batería adversarial y las métricas por subgrupo apuntan en la misma dirección. Pero el corte por sí solo no tiene potencia estadística, y la conclusión sobre equidad dialectal no debería considerarse cerrada hasta recolectar más ejemplos reales. Es una de las líneas de trabajo pendientes.

---

### D2 ⚠ — El sistema falla ante ironía y sarcasmo. ¿Sirve para el debate político salvadoreño?

Es el sesgo más severo que queda y hay que decirlo sin matizar: **tal como está, un sistema desplegado sobre este dominio sobre-bloquearía la ironía.**

El F1-macro cae a 0.4947 ante sarcasmo y 0.5250 ante ironía, unos treinta y cuatro puntos por debajo de los textos sin figura retórica. Es el doble que la brecha entre plataformas.

Por eso el uso que recomendamos es apoyo a la revisión humana y nunca moderación autónoma. Un sistema que prioriza qué revisa una persona puede tolerar ese error, porque la persona lo corrige. Un sistema que bloquea, no.

La causa probable es de datos: los cortes de sarcasmo e ironía tienen 32 y 31 casos respectivamente, y las figuras retóricas exigen contexto conversacional que nuestro modelo no ve, porque evalúa publicaciones aisladas.

---

### D3 — ¿Qué significa que la calibración sea mala y por qué importa?

Significa que las probabilidades que devuelve el sistema no son probabilidades reales. Cuando declara noventa por ciento de confianza, acierta menos del noventa por ciento.

El error de calibración esperado es 0.1214. Mejoró respecto al 0.1640 del modelo anterior, pero sigue siendo alto.

Importa porque la salida está pensada para presentarse a un moderador humano. Un número de confianza alto induce exceso de confianza en quien lo lee. Por eso lo declaramos explícitamente en las consideraciones éticas: **las confianzas del prototipo no deben interpretarse como probabilidades.**

La corrección conocida sería aplicar escalado de temperatura o de Platt sobre la salida softmax. No lo hicimos en esta etapa y queda como trabajo futuro.

---

### D4 ⚠ — ¿Por qué rechazaron el filtro de reglas si reducía los falsos positivos?

Porque reducía los falsos positivos **por construcción, sin que el modelo hubiera aprendido nada**, y abría una vía de evasión trivial.

Una regla que solo puede mover predicciones hacia No Tóxico baja el FPR mecánicamente. La métrica mejora; el sistema no.

Y lo medimos. Con cien amenazas y seis prefijos afectivos: sin prefijo, el prototipo con reglas dejaba pasar una de cien. Anteponiendo «gracias», dejaba pasar **veinte de cien**. La regla convertía el marcador afectivo en una llave.

El modelo de esta etapa, sin ninguna capa de reglas, pasa de tres a cinco de cien con el mismo prefijo: la sensibilidad normal de cualquier clasificador al contexto. Sin capa de reglas no hay puerta trasera.

---

### D5 — ¿Qué riesgos tiene desplegar este sistema?

Cuatro, y los tenemos documentados.

El primero es el sobre-bloqueo del habla local: aunque mejoró, el FPR con jerga salvadoreña sigue en 27.6 %. El segundo es la ironía y el sarcasmo, que es el punto débil medido. El tercero es la calibración: confianzas que no reflejan incertidumbre real. Y el cuarto es que el modelo no ve contexto conversacional —evalúa publicaciones aisladas— y buena parte del acoso real es acumulativo y distribuido entre varias publicaciones.

Por eso la conclusión del trabajo es explícita: el sistema queda listo como instrumento de investigación y de priorización, no como decisor. Automatizar moderación sobre una base de 2,144 ejemplos reales habría sido imprudente.

---

### D6 — ¿Cómo manejaron los datos personales del corpus?

Los autores quedaron seudonimizados y las URLs de origen quedaron fuera del corpus distribuido. Las menciones se reemplazan por un marcador en la normalización.

Un detalle de ese proceso que vale la pena mencionar porque fue un defecto que corregimos: la anonimización de menciones no exigía límite de palabra, de modo que «m@tar» se convertía en «m@usuario» y destruía en la normalización precisamente una de las ofuscaciones que queríamos detectar. Se añadió la guarda correspondiente.

---

# E. Sobre el prototipo

### E1 — ¿El prototipo usa el mismo preprocesamiento que el entrenamiento?

Sí, y fue la decisión de diseño central.

El endpoint **importa la función de normalización del mismo módulo** que preparó el entrenamiento. No hay una segunda implementación que pueda divergir.

El problema que eso evita tiene nombre: *train/serve skew*. Si el texto se limpia de una forma al entrenar y de otra al servir, las métricas del informe describen un sistema distinto del que está corriendo en producción. Fue un problema que tuvimos en la Etapa I.

La interfaz además muestra en pantalla el texto tal como lo recibe el modelo después de normalizar, para que el comportamiento sea auditable sin leer el código.

---

### E2 — ¿Cuál es el rendimiento del prototipo? ¿Soportaría uso real?

El modelo tiene 109 millones de parámetros y se entrena completo en minuto y medio en una tarjeta gráfica de consumo. En inferencia el endpoint de lote acepta hasta 64 textos por petición.

No hicimos pruebas de carga ni medimos latencia bajo concurrencia, así que no puedo darle una cifra de capacidad. Es una limitación del alcance: el prototipo demuestra el contrato de inferencia y la paridad con el entrenamiento, no está dimensionado para producción.

---

### E3 — ¿Por qué el sistema devuelve las cuatro probabilidades y no solo la clase?

Por transparencia hacia el revisor humano. Si la decisión final la toma una persona, esa persona necesita ver si el sistema estaba dudando entre ofensivo y odio, que es justamente la frontera difícil, o si la predicción era clara.

Con la salvedad que ya mencioné: esas probabilidades no están bien calibradas y no deben leerse como certezas.

---

# F. Preguntas de marco y cierre

### F1 — ¿Qué haría distinto si empezara de nuevo?

Tres cosas, en este orden.

Primero, **medir antes de elegir.** En la Etapa I elegimos dos arquitecturas por convención y resultaron ser las dos peores de siete. La comparación controlada cuesta pocas horas y nos habría ahorrado una etapa completa.

Segundo, **invertir en etiquetas antes que en modelos.** El acuerdo entre anotadores, 0.8095, es el techo del problema, y lo supimos tarde.

Y tercero, **diseñar las pruebas de diagnóstico junto con el generador de datos, no después.** El atajo sintáctico existió porque el generador y las pruebas se construyeron con la misma idea de qué podía fallar. Si las hubiéramos diseñado de forma independiente, lo habríamos visto antes.

---

### F2 — ¿Cuál es el siguiente paso concreto?

Ampliar el corpus real y mejorar la anotación, en ese orden. Todo lo demás está limitado por ahí.

En concreto: llegar a 771 ejemplos reales por clase, que no alcanzamos en Discurso de Odio ni en Amenazas; recolectar casos reales de emojis de amenaza, que hoy tienen cobertura cien por ciento sintética; y ampliar el conjunto de prueba, porque con 460 instancias no podemos distinguir diferencias de dos o tres puntos entre sistemas.

Después de eso, dos mejoras técnicas identificadas: calibración por escalado de temperatura, y trabajar el contexto conversacional para atacar las figuras retóricas.

---

### F3 — ¿Cuál fue su aporte personal en el trabajo?

*(Responder con lo que efectivamente hiciste. Guía de lo que consta en el proyecto:)*

Mi responsabilidad fue el componente de datos y la verificación. En concreto: la normalización unificada que usan entrenamiento, evaluación e inferencia; la construcción del corpus dirigido y su higiene, incluida la detección de las siete filas de fuga; la auditoría de los modelos de la Etapa I, con reejecución independiente de los checkpoints y contraste entre cifra publicada y cifra reproducida; la batería adversarial de 144 casos; y la comparación estadística pareada entre sistemas.

La auditoría fue la que derivó en dos de los hallazgos que expuse: la contaminación del conjunto de prueba y la vulnerabilidad del filtro de reglas.

---

### F4 — ¿Este trabajo es replicable?

Sí. El repositorio está en la última diapositiva, rama v3, con el código, el corpus, los informes y los artefactos de evaluación. El reporte incluye una tabla con el comando exacto que reproduce cada sección.

Todos los scripts son deterministas con semilla fija. Los pesos del modelo no se versionaron por exceder el límite de tamaño de la plataforma, pero el manifiesto incluye su SHA-256 de referencia, y las funciones resumen de validación y prueba están publicadas para que cualquiera verifique que no se modificaron.

---

# G. Si se complica

### Si preguntan algo que no medimos

> «Eso no lo medimos en esta etapa, así que no puedo darle una cifra sin inventarla. La forma de medirlo sería [X], y queda anotado.»

### Si señalan un error que es real

> «Tiene razón, es un error nuestro. El valor correcto es [X] y está en la Tabla [N]. La conclusión que se sostiene es [Y].»

### Si cuestionan la utilidad del trabajo

> «Un clasificador no resuelve el discurso de odio. Lo que aporta este trabajo son tres cosas medibles: un corpus salvadoreño etiquetado que no existía, evidencia de que el preentrenamiento de dominio importa más que el tamaño del modelo —lo que abarata cualquier implementación posterior— y una metodología de auditoría aplicable a cualquier sistema de moderación antes de confiar en él.»

### Si insisten en un punto ya concedido

No repitas el argumento con otras palabras. Reconocé y pasá:

> «Coincido, es una limitación real del trabajo y está declarada en el reporte. ¿Hay algo más de ese punto que quiera que profundice?»

### Si te quedás en blanco

> «Permítame ordenar la respuesta un momento.»

Tres segundos de silencio se ven mejor que una respuesta improvisada. No te disculpes por pensar.

---

## Las seis cifras que tenés que tener en la punta de la lengua

| Pregunta implícita | Respuesta |
|---|---|
| ¿Cuánto dio? | **0.8529**, IC [0.8191, 0.8858] |
| ¿Y sin el ensemble? | 0.8268, IC [0.7912, 0.8610] — cruza la meta |
| ¿Cuántos datos reales? | **2,144** de entrenamiento; prueba 460 |
| ¿Cuánto bajó el sesgo? | 41–45 % → **27.6 %**, pero n = 29 |
| ¿Qué tan buenas son las etiquetas? | Acuerdo de **0.8095** entre anotadores |
| ¿Cuál es el peor punto? | Ironía **0.5250**, sarcasmo **0.4947** |
