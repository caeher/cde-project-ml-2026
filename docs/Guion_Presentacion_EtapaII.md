# Guion de presentación — Etapa II

**Expositor:** Willian Alexander Chávez Servellón
**Duración:** 30 minutos de exposición + 15 de preguntas
**Diapositivas:** 16

---

## ⚠ Leer esto antes de ensayar

Encontré **ocho discrepancias** entre el reporte y sus propias tablas. Tres son importantes porque un jurado que revise las tablas las va a ver. **El guion ya está escrito con la versión defendible de cada una** — no repite ninguna. Pero conviene que las conozcas por si preguntan.

### Las tres graves

**1. «Ambos por encima de 0.80» es falso para el modelo individual.**

La sección 12.2 dice: *«el extremo inferior del intervalo del ensemble se situó en 0.8191 y el del modelo individual en 0.7912, ambos por encima de 0.80»*. **0.7912 no está por encima de 0.80.** Y la Tabla 13 marca al modelo individual con «¿Meta con IC? Sí», mientras marca a TwitterXLM-R con 0.7940 como «No» — con el mismo criterio, ambos deberían ser «No».

→ En el guion solo se afirma la meta para el **ensemble** (0.8191). Si preguntan por el individual, la respuesta honesta es que su intervalo cruza la meta y que por eso el sistema propuesto es el ensemble.

**2. «Las tres comparaciones fueron estadísticamente significativas» es falso.**

La Tabla 15 da p = 0.2820 (vs XLM-R v1), p = 0.0026 (vs mBERT B2) y p = 0.0567 (vs XLM-R mitigado). **Solo una de las tres** es significativa a α = 0.05.

→ El guion dice lo correcto: significativa frente a mBERT B2, marginal frente al mitigado, y no concluyente frente a XLM-R v1.

**3. Las métricas por clase de la prosa no coinciden con la Tabla 14.**

El texto dice *«Las cuatro clases superaron 0.83»*, *«Discurso de Odio… subió a 0.8308»* y *«Amenazas/Violencia… hasta 0.8488»*. La Tabla 14 dice **0.8020** y **0.8293**. Probablemente la prosa describe el ensemble y la tabla el modelo individual, pero no se aclara.

→ El guion usa los valores de la Tabla 14 y dice explícitamente que son del modelo individual.

### Las cinco menores

| # | Dónde | Qué pasa |
|---|---|---|
| 4 | Tabla 8 vs prosa §10 | La tabla dice «Épocas finales solo con reales: **0**»; el texto siguiente dice «**tres** épocas finales únicamente con ejemplos reales» |
| 5 | Tabla 16 vs Tabla 20 | Batería adversarial: 125/144 y sonda 200/204 en una; 127/144 y 202/204 en la otra, para el mismo modelo final |
| 6 | Tabla 10 vs prosa §11.2 | La semilla 2026 aparece como 0.8555 en la tabla y 0.8562 en el texto |
| 7 | Tabla 11 | Se titula «seis mejores» y lista cuatro filas |
| 8 | Tabla 21 | Las filas de sarcasmo suman 402, ironía 432 y contexto político 369, no 460. Faltan los nulos y no se explica |

**Si se puede, corregí 1, 2 y 3 en el reporte antes de entregarlo.** Son de redacción, no de resultados: los números buenos ya están en las tablas.

---

## Distribución del tiempo

| Diap. | Tema | Min | Acumulado |
|---|---|---|---|
| 1 | Portada | 0:30 | 0:30 |
| 2 | Agenda | 0:40 | 1:10 |
| 3 | Problema y taxonomía | 2:10 | 3:20 |
| 4 | Metodología | 1:50 | 5:10 |
| 5 | Corpus | 2:10 | 7:20 |
| 6 | Dominio vs. tamaño | 2:30 | 9:50 |
| 7 | Optuna | 2:00 | 11:50 |
| 8 | Ensemble | 2:00 | 13:50 |
| 9 | Resultado principal | 2:40 | 16:30 |
| 10 | Desempeño por clase | 1:50 | 18:20 |
| 11 | Auditoría y atajo | 3:00 | 21:20 |
| 12 | Equidad | 2:40 | 24:00 |
| 13 | Demo | 2:20 | 26:20 |
| 14 | Impacto | 1:40 | 28:00 |
| 15 | Conclusiones | 1:40 | 29:40 |
| 16 | Preguntas | 0:20 | **30:00** |

**Ritmo:** unas 145 palabras por minuto. Si vas adelantado, alargá la diapositiva 11 (es la más fuerte). Si vas atrasado, recortá la 14 — es la más prescindible.

---

# GUION

---

## Diapositiva 1 — Portada · 0:30

> *[Esperar a tener la atención de la mesa. No empezar hablando.]*

Buenos días. Muchas gracias por su tiempo.

Mi nombre es Willian Alexander Chávez Servellón y, junto con mis compañeros Cristian Escalante y Julio De La Quadra, presento la Etapa II del trabajo «Análisis del discurso de odio en redes sociales de El Salvador».

En esta etapa pasamos del modelado inicial a un sistema evaluado, auditado y funcionando. Lo que van a ver en los próximos treinta minutos incluye tanto lo que funcionó como lo que no, porque en este caso lo segundo resultó igual de informativo.

> *[Avanzar]*

---

## Diapositiva 2 — Agenda · 0:40

El recorrido es el siguiente.

Primero el problema y el objetivo verificable que nos fijamos. Segundo, los datos y la metodología: cómo se construyó el corpus y qué controles de calidad se aplicaron. Tercero, el modelado: la comparación de arquitecturas y la optimización. Cuarto, la evaluación, donde entra el análisis de sesgos y las consideraciones éticas. Y quinto, la demostración del prototipo, el impacto social y las conclusiones.

Les pido que reserven las preguntas para el final, donde tenemos quince minutos.

> *[Avanzar]*

---

## Diapositiva 3 — Problema, objetivo y taxonomía · 2:10

El problema de partida es concreto y lo medimos, no lo supusimos.

Las herramientas de moderación que operan sobre las redes sociales salvadoreñas están entrenadas en español general. Nuestra Etapa I mostró que esos modelos no leen bien el registro local: marcaban como tóxico entre el cuarenta y uno y el cuarenta y cinco por ciento de los textos **inofensivos** que contenían jerga salvadoreña, frente al dieciséis por ciento de sus equivalentes en español estándar.

Dicho de otro modo: hablar como se habla en El Salvador multiplicaba por dos punto siete la probabilidad de ser silenciado por error.

> *[Pausa breve. Es el dato que justifica todo el trabajo.]*

El objetivo que nos fijamos fue verificable, no cualitativo: alcanzar un F1-macro de al menos cero punto ochenta sobre el conjunto de prueba, y sostenerlo con evidencia estadística, con pruebas de robustez y con un análisis de equidad. No bastaba con llegar a la cifra: había que demostrar que la cifra significaba algo.

La taxonomía tiene cuatro niveles ordenados por gravedad: no tóxico, lenguaje ofensivo, discurso de odio y amenazas o violencia.

Dos precisiones sobre la taxonomía. La primera: cada texto recibe **una sola** etiqueta. La segunda: cuando un texto podría caer en dos niveles, se aplica precedencia por severidad, se asigna el más grave.

La distinción que más cuesta es la segunda contra la tercera. Lenguaje ofensivo es un insulto sin grupo protegido de por medio; discurso de odio es un ataque a alguien **por pertenecer** a un grupo protegido. «Sos un estúpido» es lo primero. «Los nicaragüenses son una plaga» es lo segundo. Van a ver que esa frontera es donde el modelo más se equivoca, y adelanto que también es donde más se equivocaban los anotadores humanos.

> *[Avanzar]*

---

## Diapositiva 4 — Metodología · 1:50

Seguimos CRISP-DM en sus fases de modelado, evaluación y despliegue, con una adición que no estaba en el plan original.

La primera etapa de este diagrama, la auditoría, **la añadimos sobre la marcha**. Al revisar los modelos de la Etapa I encontramos dos cosas que obligaban a detenerse: filas de entrenamiento que coincidían con el conjunto de prueba, y una vulnerabilidad en el prototipo que permitía evadir la clasificación con una sola palabra. Vamos a volver sobre esto en detalle más adelante.

Después vienen las cuatro fases planificadas. Datos: un corpus dirigido a los errores que la auditoría había medido, con una normalización unificada. Modelado: la comparación controlada de siete arquitecturas, con optimización de hiperparámetros. Evaluación: validación cruzada, prueba final, robustez y equidad. Y despliegue: una API en FastAPI con una interfaz web.

La decisión metodológica que atraviesa todo el trabajo es esta: **cada mejora que reportamos tuvo que sobrevivir a una prueba estadística pareada.** En la Etapa I habíamos reportado mejoras que, al medirlas bien, resultaron ser del mismo tamaño que el ruido de inicialización del modelo. No queríamos repetirlo.

> *[Avanzar]*

---

## Diapositiva 5 — Corpus dirigido y control de calidad · 2:10

El corpus de entrenamiento quedó en seis mil cuatrocientos dieciséis registros, compuesto de tres partes: dos mil ciento cuarenta y cuatro publicaciones reales, mil ciento cuarenta ejemplos sintéticos de la versión anterior, y tres mil ciento treinta y dos sintéticos nuevos generados específicamente para esta etapa.

La palabra importante ahí es **dirigidos**. No generamos volumen: generamos ejemplos para cuatro debilidades que ya habíamos medido.

Primera: amenazas ofuscadas y *leetspeak*, escribir «matar» con un cuatro en lugar de la «a». Segunda: eufemismos locales de violencia, expresiones como «dar piso» o «dar cuello», que un modelo entrenado en español general no reconoce. Tercera: emojis usados como vehículo de ataque, y su normalización consistente. Cuarta: falsos positivos ante jerga inofensiva.

El material de partida no fue inventado. Fue un léxico salvadoreño de ciento diez familias con mil novecientas setenta y nueve variantes de ofuscación, **observadas en el corpus real**.

> *[Señalar la línea inferior de la diapositiva]*

Y quiero subrayar la línea de abajo, porque es la condición que hace válido todo lo que viene después. **Los conjuntos de validación y prueba no se tocaron.** Cuatrocientos cincuenta y nueve y cuatrocientos sesenta registros, sin modificar una sola etiqueta ni renormalizar un solo texto. Verificamos sus funciones resumen SHA-256 contra las de la Etapa I y coinciden.

Eso significa que cuando comparemos el modelo de esta etapa con los de la anterior, la comparación es legítima: ninguna mejora puede atribuirse a haber facilitado la prueba.

Además verificamos que ningún texto de entrenamiento aparece en validación, en prueba ni en la batería adversarial. Esa verificación detectó siete filas que el proyecto arrastraba desde agosto y que quedaron fuera.

> *[Avanzar]*

---

## Diapositiva 6 — El dominio de preentrenamiento importó más que el tamaño · 2:30

Este es, a mi juicio, el hallazgo más transferible del trabajo.

Comparamos siete arquitecturas bajo condiciones idénticas: mismo corpus, mismos hiperparámetros, mismo conjunto de validación. mBERT multilingüe, BETO, BERTIN, RoBERTuito, XLM-RoBERTa en sus versiones base y large, y TwitterXLM-R.

El resultado fue que **el tamaño del modelo no explicó el desempeño.**

XLM-R large tiene quinientos sesenta millones de parámetros. RoBERTuito tiene ciento nueve, cinco veces menos. El grande obtuvo cero punto ocho cero nueve de F1-macro; el pequeño, cero punto ocho dos siete dos. Y tardó **veintiocho veces más** en entrenarse: cuarenta y dos minutos contra uno y medio.

> *[Pausa]*

Lo que sí separó a los dos mejores del resto fue el **corpus de preentrenamiento**. Los dos primeros, TwitterXLM-R y RoBERTuito, habían sido preentrenados sobre publicaciones de redes sociales en español. Los demás, sobre texto general.

Y hay una comparación que lo aísla de forma limpia. TwitterXLM-R es exactamente la misma arquitectura que XLM-R base: mismo tamaño, mismo tokenizador, mismo todo. La única diferencia es el corpus sobre el que fue preentrenado. Le saca cero punto cero tres nueve de F1-macro. Esa diferencia no puede atribuirse a nada más.

Lo medimos también antes de entrenar, con la fertilidad del tokenizador, que es cuántos subtokens necesita para representar una palabra. RoBERTuito necesitaba uno punto cuarenta y siete; mBERT, uno punto ochenta, un veintitrés por ciento más de fragmentación sobre el mismo texto. En mBERT, «cerote» se parte en «cero» y «te», «maje» en «maj» y «e», «pisto» en «pis» y «to». El modelo nunca ve la palabra.

Tengo que decirlo con claridad porque es incómodo: **los dos modelos que elegimos en la Etapa I resultaron ser los dos peores de los siete.** mBERT quedó último con cero punto siete seis tres seis. Esa elección, que se había hecho por convención, nos costó cerca de cuatro puntos de F1-macro.

> *[Avanzar]*

---

## Diapositiva 7 — Optimización con Optuna · 2:00

La segunda fuente de mejora fue optimizar los hiperparámetros, algo que en la Etapa I nunca se había hecho: se habían fijado por convención.

Ejecutamos veinte pruebas con Optuna usando un muestreador TPE con semilla fija, optimizando F1-macro **sobre el conjunto de validación**. Quiero ser explícito en esto: **el conjunto de prueba no participó en la búsqueda ni se consultó durante ella.**

La configuración por defecto daba cero punto ocho dos siete dos. La mejor prueba llegó a cero punto ocho cinco cuatro nueve. La aportación de la búsqueda fue de **más cero punto cero dos cinco**.

Pero el número que me parece más informativo no es ese, sino el rango: entre la mejor y la peor configuración hubo cero punto cero cuatro ocho de diferencia, casi cinco puntos de F1. Eso dimensiona el riesgo de fijar los hiperparámetros por convención, que es exactamente lo que se había hecho hasta entonces.

La configuración ganadora tiene un detalle que vale la pena explicar: una tasa de aprendizaje de cinco punto siete tres por diez a la menos cinco, lotes de treinta y dos, seis épocas, y un **peso de cero punto setenta y cinco para los ejemplos sintéticos**. Es decir, el proceso decidió por sí solo que los sintéticos debían pesar menos que los datos reales. No se lo impusimos: salió de la búsqueda.

> *[Avanzar]*

---

## Diapositiva 8 — Modelo final: RoBERTuito con ensemble de tres semillas · 2:00

El modelo final fue RoBERTuito con la configuración óptima, entrenado con tres semillas distintas.

Sobre validación, la semilla cuarenta y dos dio cero punto ocho tres siete cuatro; la mil trescientos treinta y siete, cero punto ocho cuatro cero nueve; y la dos mil veintiséis, cero punto ocho cinco cinco cinco.

> *[Pausa. Este punto es el que más respeto metodológico gana.]*

Ahí hay una lección que quiero destacar. La dispersión entre semillas fue de **uno punto ocho puntos** de F1-macro. Y ese número hay que tenerlo presente al leer cualquier comparación de este proyecto: varias de las «mejoras» que se reportaron en entregas anteriores eran del mismo orden de magnitud que el ruido de la inicialización aleatoria. No eran mejoras: era azar.

Por eso el sistema propuesto **no es la mejor semilla**. Es el promedio de las tres, por voto blando: se promedian las probabilidades de las tres ejecuciones.

Y la regla se fijó **antes** de mirar el conjunto de prueba. Podríamos haber elegido la semilla dos mil veintiséis, que era la mejor sobre validación. No lo hicimos por dos razones. La primera es que cualquier criterio de selección, incluso sobre validación, reintroduce el sesgo de quedarse con la combinación afortunada. La segunda es más concreta: esa semilla conservaba cuatro falsos positivos en una sonda de diagnóstico. Elegirla habría sido seleccionar precisamente por la métrica que no veía el defecto.

> *[Avanzar]*

---

## Diapositiva 9 — La meta se cumplió con respaldo estadístico · 2:40

Este es el resultado principal.

Sobre el conjunto de prueba, cuatrocientas sesenta instancias consultadas **una sola vez** con los modelos ya seleccionados, el ensemble obtuvo un **F1-macro de cero punto ocho cinco dos nueve**, con un intervalo de confianza del noventa y cinco por ciento de cero punto ocho uno nueve uno a cero punto ocho ocho cinco ocho. Trescientos noventa y cuatro aciertos de cuatrocientos sesenta.

> *[Pausa]*

Quiero detenerme en por qué reportamos el intervalo y no solo la cifra.

El criterio exigente que nos fijamos no era superar cero punto ochenta con la estimación puntual. Era superarlo con **el extremo inferior del intervalo**. El extremo inferior del ensemble está en cero punto ocho uno nueve uno. Es decir: no pasó solo el punto; pasó el intervalo completo.

Esa distinción importa porque, de los siete sistemas que evaluamos, cuatro cruzaban la meta con su intervalo. Cruzarla significa que **ni la superan ni la descartan**: con este tamaño de prueba no se puede afirmar nada sobre ellos. Solo los sistemas de esta etapa quedaron enteramente por encima de la línea.

> *[Señalar la validación cruzada]*

El segundo respaldo es la validación cruzada: cinco pliegues estratificados sobre entrenamiento y validación unidos, con media de cero punto ocho dos siete cuatro y desviación de cero punto cero uno siete cero.

Dos detalles de cómo se hizo. Primero: los ejemplos sintéticos se asignaron **siempre** al lado de entrenamiento y nunca aparecieron en el pliegue de evaluación. Cada pliegue se evaluó exclusivamente sobre publicaciones reales, dos mil seiscientas tres en total. Medir sobre texto de plantilla habría inflado la métrica artificialmente.

Segundo, y esto es una advertencia honesta: el rango entre pliegues fue de cero punto ocho uno dos ocho a cero punto ocho cinco seis cero. Casi cuatro puntos y medio. Con un corpus de este tamaño, **la partición concreta influye en el resultado**, y eso refuerza la necesidad de reportar intervalos en lugar de una cifra única.

> *[Si preguntan por el modelo individual: su intervalo va de 0.7912 a 0.8610, es decir, cruza la meta. Por eso el sistema propuesto es el ensemble y no el individual.]*

> *[Avanzar]*

---

## Diapositiva 10 — Desempeño por clase · 1:50

Estas son las métricas por clase del modelo individual sobre el conjunto de prueba.

No tóxico: F1 de cero punto ocho cuatro uno dos. Lenguaje ofensivo: cero punto ocho tres cuatro nueve. Discurso de odio: cero punto ocho cero dos cero. Amenazas y violencia: cero punto ocho dos nueve tres.

Lo relevante no es solo que las cuatro estén por encima de cero punto ochenta. Es que **Discurso de Odio dejó de ser el punto débil**. En todos los modelos anteriores del proyecto esa clase estaba entre cero punto siete tres y cero punto ocho cero; ahora es comparable con las demás. Era la clase que más nos preocupaba, porque es la que define la tarea.

> *[Señalar la matriz de confusión]*

Sobre el patrón de error, dos observaciones.

La confusión principal ocurre entre **lenguaje ofensivo y discurso de odio**, que son clases contiguas en la escala de gravedad. Es el mismo límite que mencioné al principio, y es también la distinción que más costaba a los anotadores humanos. No es un defecto del modelo: es una dificultad de la tarea.

La segunda observación es la que importa para un uso de moderación: **los errores de dos o más niveles fueron escasos.** El sistema casi nunca clasifica una amenaza como no tóxica, ni al revés. Cuando se equivoca, se equivoca de grado, no de categoría. Para una herramienta cuya función es priorizar qué revisa una persona, eso es exactamente lo que se necesita.

> *[Avanzar]*

---

## Diapositiva 11 — Auditoría: una métrica alta no detecta todos los atajos · 3:00

Esta diapositiva es la que más me interesa exponer, porque recoge la lección metodológica del trabajo.

Al probar el prototipo con la frase **«voy a comer»** —tres palabras, sin ninguna carga— el sistema la clasificó como Amenazas y Violencia con un ochenta y dos coma seis por ciento de confianza.

> *[Pausa. Dejar que el absurdo se asiente.]*

Investigamos el caso y lo que encontramos fue esto: el modelo **no había aprendido los verbos violentos. Había aprendido la construcción sintáctica que los envolvía.** La estructura «te voy a», más un verbo.

¿Por qué? Porque nuestro generador rellenaba esa construcción únicamente con verbos de agresión. En el corpus dirigido, antes del arreglo, la construcción aparecía en cuarenta y siete filas, y en cuarenta y cinco de ellas estaba etiquetada como Amenaza. **En ninguna estaba etiquetada como No Tóxico.** Sin un solo contraejemplo, aprender la construcción en lugar del significado era la solución más barata, y el modelo la tomó.

Y hay un dato que lo vuelve más serio. Medimos la probabilidad media de amenaza sobre siete frases inocuas: en los modelos de la Etapa I, que no tenían ningún sintético, era del catorce y del treinta y cinco por ciento. En los modelos con sintéticos subía al sesenta y siete y al ochenta por ciento. **El defecto entró con los ejemplos sintéticos y se agravó con cada ampliación del corpus.** Era una propiedad del método de aumento por plantilla, no de una implementación concreta.

> *[Pausa]*

Ahora, la parte que considero central: **ninguna métrica lo detectó.**

Las construcciones afectadas aparecían en catorce de las cuatrocientas sesenta instancias de prueba. Un tres por ciento. Un modelo podía tener el atajo completamente instalado sin perder prácticamente nada de F1-macro, porque la prueba no ejercitaba esa zona. Ni la batería adversarial ni la sonda dirigida lo cubrían: ambas se habían diseñado contra la ofuscación, los emojis y el sesgo dialectal.

La lección es esa, y aplica a todo el proyecto: **una métrica agregada sobre un conjunto que no muestrea el modo de fallo no lo ve, por alta que sea la cifra.**

La corrección fue conceptualmente simple. Añadimos al generador los mismos portadores de amenaza, sin modificarlos, rellenados con quince verbos inocuos que admiten la misma morfología —llamar, invitar, ayudar, esperar, visitar, saludar— y etiquetados como No Tóxico. Doscientas diecinueve filas.

Excluimos el verbo «buscar» a propósito, porque «te voy a buscar» **sí** se usa como amenaza y la batería adversarial lo tenía etiquetado así. Enseñarlo como inocuo habría introducido una contradicción en el corpus.

El resultado: la probabilidad media de amenaza en frases inocuas cayó del cincuenta y tres al **uno coma seis por ciento**, mientras que en amenazas reales se mantuvo en el cien por ciento. Los falsos positivos de la sonda pasaron de trece a **cero**, y no se perdió ninguna amenaza.

De ahí salió la regla que quedó incorporada al diseño del generador: **toda estructura usada para producir una clase debe aparecer también, con relleno distinto, produciendo otra.** Si no, el modelo aprende la estructura.

> *[Señalar el caso de evasión de la diapositiva]*

El segundo hallazgo de la auditoría fue una vulnerabilidad. El prototipo anterior incorporaba un filtro de reglas para corregir el sesgo dialectal: si un texto clasificado como ofensivo contenía un marcador afectivo —«gracias», «qué onda», «mi hermano»— se reasignaba a No Tóxico.

Lo probamos con cien amenazas y seis prefijos. Sin prefijo, el prototipo dejaba pasar una de cien. Anteponiendo «gracias», dejaba pasar **veinte de cien**. La regla convertía el marcador afectivo en una llave.

El modelo de esta etapa, sin ninguna capa de reglas, pasa de tres a cinco de cien con el mismo prefijo: la sensibilidad normal de cualquier clasificador al contexto. **Sin capa de reglas no hay puerta trasera.**

Las decisiones que tomamos a partir de la auditoría están en la diapositiva: se eliminaron las reglas post-hoc, se unificó la normalización entre entrenamiento e inferencia, se añadieron pruebas adversariales al pipeline, y se revisó la contaminación del conjunto de prueba.

> *[Avanzar]*

---

## Diapositiva 12 — Equidad: mejoró el sesgo dialectal, pero persisten brechas · 2:40

Vuelvo al problema con el que abrí, porque es donde se mide si el trabajo sirvió.

La tasa de falsos positivos sobre textos inofensivos con jerga salvadoreña pasó del cuarenta y uno al cuarenta y cinco por ciento en los modelos de la Etapa I, al **veintisiete coma seis por ciento** en el modelo propuesto. La brecha respecto al español estándar se redujo aproximadamente a la mitad. Es la primera vez en el proyecto que el sesgo dialectal se reduce **sobre datos reales** y no solo sobre ejemplos sintéticos.

> *[Pausa y cambio de tono. Esta advertencia hay que darla sin que la pregunten.]*

Ahora, con la misma claridad: **ese corte tiene veintinueve casos.** Un solo ejemplo mueve la métrica tres coma cuatro puntos. La tendencia es consistente con el resto de las mediciones, pero el corte por sí solo no tiene potencia estadística, y por eso **no presentamos la conclusión sobre equidad dialectal como definitiva.** Queda pendiente recolectar más ejemplos reales.

Prefiero decirlo yo a que me lo pregunten.

> *[Señalar las brechas pendientes]*

Y quedan brechas que no resolvimos.

La más severa son las **figuras retóricas**. Ante sarcasmo el F1-macro cae a cero punto cuatro nueve; ante ironía, a cero punto cincuenta y dos. Son caídas de treinta y cuatro puntos respecto a los textos sin figura retórica: el doble que la brecha entre plataformas. Y afecta a un fenómeno muy frecuente en el registro coloquial salvadoreño. Un sistema desplegado sobre este dominio **sobre-bloquearía la ironía**. Es el sesgo más grave que queda abierto.

La brecha entre plataformas persiste: cero punto setenta y seis en Facebook contra cero punto noventa y uno en X. Nuestra lectura es que es un problema de composición del corpus, no de modelado: los textos de Facebook son más largos, con varios hilos y sintaxis más compleja, y están peor representados.

Y la calibración. El error de calibración esperado es de cero punto doce uno cuatro. Mejoró respecto al cero punto dieciséis de la etapa anterior, pero sigue lejos de ser fiable: la curva queda por debajo de la diagonal en casi todo el rango, es decir, **cuando el sistema declara noventa por ciento de confianza, acierta menos del noventa por ciento.**

La implicación práctica es directa y quiero dejarla dicha: **las confianzas que devuelve el prototipo no deben leerse como probabilidades**, y por eso ninguna decisión que afecte a una persona debería tomarse solo con esta salida.

> *[Avanzar]*

---

## Diapositiva 13 — Demo del prototipo funcional · 2:20

> *[Si la demo es en vivo: abrir antes de hablar y dejar la pestaña cargada. Si falla, seguir con la tabla del reporte sin disculparse demasiado.]*

El prototipo es una API construida con FastAPI, con una interfaz web.

La decisión de diseño central no está a la vista pero es la que sostiene todo lo anterior: **el endpoint importa la función de normalización del mismo módulo que preparó el entrenamiento.** No hay una segunda implementación que pueda divergir.

Eso resuelve un problema que en la Etapa I nos costó caro y que tiene nombre propio: *train/serve skew*. Si el texto se limpia de una forma al entrenar y de otra al servir, las métricas del informe describen un sistema distinto del que está corriendo. Con una sola fuente de verdad, lo que medimos es lo que ocurre.

Hay cuatro rutas: salud, que devuelve el estado y el contrato de inferencia; clasificar, para un texto; clasificar-lote, hasta sesenta y cuatro textos por petición; y la interfaz web.

> *[Ejecutar los tres casos en este orden]*

Voy a probar tres casos.

El primero, jerga salvadoreña inofensiva: **«Qué onda maje, todo bien por allá».** No tóxico. Es el caso que los modelos de la Etapa I marcaban como ofensivo.

El segundo, discurso de odio real: **«Los nicaragüenses son una plaga».** Discurso de odio, con el desglose de las cuatro probabilidades.

Y el tercero, el que justifica la auditoría: **«gracias, te voy a matar».** Esta es exactamente la frase que evadía al prototipo de la Etapa I, que la clasificaba como No Tóxico porque la regla veía «gracias». El modelo actual la clasifica como **Amenaza**.

> *[Señalar el texto normalizado en pantalla]*

La interfaz muestra, además de la clase y las probabilidades, **el texto exactamente como lo recibe el modelo tras la normalización**. Lo pusimos ahí a propósito: permite auditar el comportamiento desde la propia pantalla, sin tener que leer el código.

> *[Avanzar]*

---

## Diapositiva 14 — Aporte social y recomendaciones · 1:40

Las recomendaciones que derivamos están ordenadas por viabilidad inmediata, y cada una se apoya en una medición del informe, no en una opinión.

A las **instituciones públicas con presencia digital**: exigir a cualquier herramienta de moderación que reporte su tasa de falsos positivos **desagregada por registro dialectal** antes de adoptarla. El fundamento es que la brecha que medimos entre jerga local y español estándar era de veintiocho puntos porcentuales en los modelos de partida.

A las **universidades y centros de investigación**: priorizar la recolección y el etiquetado de corpus locales por encima de la adopción de modelos cada vez mayores. El fundamento es el hallazgo de la diapositiva seis: un modelo de ciento nueve millones de parámetros superó a uno de quinientos sesenta millones. El cuello de botella medido fue el corpus, no la capacidad.

A las **plataformas**: publicar auditorías de equidad por variedad lingüística, no solo por idioma. El español de El Salvador se comporta como un dominio distinto del español general, y lo demostramos con datos.

A los **medios y gestores de comunidad**: usar sistemas como este para priorizar la revisión humana, nunca para bloquear automáticamente.

> *[Leer la línea inferior sin prisa]*

Y esa última idea resume nuestra posición: **un clasificador no resuelve el discurso de odio. Ayuda a medirlo y a decidir dónde mira una persona.**

> *[Avanzar]*

---

## Diapositiva 15 — Conclusiones · 1:40

Cuatro conclusiones.

**Primera: la meta se alcanzó con el criterio exigente.** F1-macro de cero punto ocho cinco dos nueve, con el intervalo de confianza completo por encima de cero punto ochenta, y una validación cruzada de cinco pliegues que lo corrobora.

**Segunda: el dominio venció al tamaño.** Un modelo de ciento nueve millones de parámetros superó a uno de quinientos sesenta millones, y lo hizo entrenándose en minuto y medio en una tarjeta gráfica de consumo. La mejora vino de cambiar de familia de modelo, no de escalar.

**Tercera: la auditoría cambió el sistema.** Corregimos fuga entre conjuntos, eliminamos una capa de reglas que abría una vía de evasión trivial, y unificamos la normalización. Ninguna de esas tres cosas se habría detectado mirando el F1-macro.

**Cuarta, y es la que quiero dejar como diagnóstico:** el siguiente salto no saldrá de más arquitectura. Seguimos con dos mil ciento cuarenta y cuatro publicaciones reales, y el acuerdo entre anotadores humanos fue de cero punto ocho cero nueve cinco. Sobre los casos en que los anotadores discreparon, el mejor modelo de la etapa anterior acertaba prácticamente al azar. **La calidad de la etiqueta es el techo real del problema.** El siguiente salto son más datos y mejores etiquetas.

> *[Leer la línea inferior mirando a la mesa]*

Y el uso recomendado, que quiero que quede constando: **apoyo a la revisión humana. Nunca moderación autónoma.**

> *[Avanzar]*

---

## Diapositiva 16 — Preguntas · 0:20

Eso es todo de mi parte.

El código, el corpus, los informes y los artefactos de evaluación están en el repositorio que aparece en pantalla, rama v3, con los comandos para reproducir cada sección del trabajo.

Quedo atento a sus preguntas. Muchas gracias.

> *[No llenar el silencio. Esperar.]*

---

# Apuntes de ejecución

## Las cinco cifras que no podés equivocar

| Cifra | Valor |
|---|---|
| F1-macro del ensemble sobre prueba | **0.8529**, IC [0.8191, 0.8858] |
| Validación cruzada | **0.8274 ± 0.0170**, 5 pliegues |
| Corpus real de entrenamiento | **2,144** publicaciones |
| FPR con jerga: antes → ahora | **41–45 % → 27.6 %** (n = 29) |
| Acuerdo entre anotadores | **0.8095** de F1-macro |

## Cuatro frases que conviene memorizar

1. «Los conjuntos de validación y prueba no se tocaron; verificamos sus SHA-256 contra los de la Etapa I.»
2. «La dispersión entre semillas fue de 1.8 puntos: varias mejoras reportadas antes eran del mismo orden que el ruido.»
3. «Una métrica agregada sobre un conjunto que no muestrea el modo de fallo no lo ve, por alta que sea la cifra.»
4. «Ese corte tiene 29 casos; un solo ejemplo mueve la métrica 3.4 puntos.»

## Reglas de sala

- **Adelantate a las debilidades.** Las diapositivas 9, 11 y 12 ya declaran los límites. Un jurado que ve que vos mismo señalás el n = 29 deja de buscar dónde te escondés.
- **Si no sabés algo, decilo.** «Eso no lo medimos» es una respuesta completa y vale más que una estimación inventada.
- **No defiendas la Etapa I.** El trabajo de esta etapa consiste precisamente en haber encontrado sus fallos. Reconocerlos es el argumento, no la concesión.
- **Cuidado con el modelo individual.** Si alguien menciona su intervalo, la respuesta correcta es que cruza la meta y que por eso el sistema propuesto es el ensemble.
- **Ensayá con cronómetro dos veces.** La diapositiva 11 tiende a alargarse porque el caso es entretenido de contar.
