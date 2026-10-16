# Prueba con 500 mensajes inventados (10 hilos x 50 respuestas)

Generado por `src/evaluation/prueba_hilos.py`; datos completos en `reports/improvement/prueba_hilos_500.csv`. Modelo: el final (`models/v3.0.0`, 5 semillas, T = 1.349), por la misma función que usa la API.

## Qué es y qué no es
- Los mensajes los escribí yo con plantillas por clase y 10 temas (selección, tráfico, precios, política, migración, lluvias, seguridad, mujeres en el trabajo, bitcoin, concierto). La etiqueta «esperada» es mi intención al escribir cada plantilla, **sin segundo anotador**.
- Ninguno coincide con train, val, test ni la batería de 144 (verificado, 0 coincidencias).
- Es una **prueba de humo de comportamiento**, no una métrica oficial. Es lenguaje de plantilla, más limpio y repetitivo que el real, así que el acierto probablemente **sobreestima** el desempeño en publicaciones reales.

## Resultado
Acierto **93.0 %** (465/500) · F1-macro **0.9293**

| esperado \ predicho | No Tóxico | Ofensivo | Odio | Amenazas |
|---|---|---|---|---|
| No Tóxico (120) | 118 | 2 | 0 | 0 |
| Ofensivo (140) | 3 | 137 | 0 | 0 |
| Odio (110) | 0 | 17 | 92 | 1 |
| Amenazas (130) | 12 | 0 | 0 | 118 |

Recall: No Tóxico 0.983 · Ofensivo 0.979 · **Odio 0.836** · **Amenazas 0.908**. Confianza media: 0.91 en aciertos, 0.70 en errores (el modelo duda más cuando se equivoca).

## Dónde falla (35 errores)
1. **Amenazas implícitas → No Tóxico (12).** Frases sin verbo violento explícito: «vamos a ir con machetes a… a arreglar esto», «le llega su hora, lo vamos a buscar a la casa», «hay que colgarlo». Las amenazas explícitas («te voy a matar», «un balazo») sí las detecta. Es la falla más seria: un falso negativo en la clase más grave.
2. **Odio contra mujeres y hondureños → Ofensivo (16 de 17 errores Odio→Ofensivo).** «Las mujeres son lo peor en la oficina» sale como insulto genérico, no como ataque a un grupo protegido. Con migrantes, indígenas, gays y venezolanos casi no falló.
3. **Dos falsos positivos raros** en «Hay que ver las dos caras de X antes de opinar» → Ofensivo.
4. **«No seas baboso, X no es tan complicado» → No Tóxico (3).** Insulto leve; mi etiqueta es discutible.

Parte de los errores de Odio vienen de mis plantillas, que a veces quedan agramaticales («algo tan una plaga»). Aun así el patrón por grupo es real.

## Hilo de muestra: «Tráfico y buses»
**Publicación original:** «Otra vez 2 horas de tráfico por el bulevar. ¿Qué opinan del sistema de buses?»

| # | Respuesta | Esperado | Predicho | |
|---|---|---|---|---|
| 1 | Qué puchica lo de el tráfico, ni modo, a seguir adelante | No Tóxico | No Tóxico (85%) | ✓ |
| 2 | voy a comer algo y ahorita les cuento qué tal el tráfico | No Tóxico | No Tóxico (98%) | ✓ |
| 3 | Compré boletos para ir a la terminal, ¿alguien más va? | No Tóxico | No Tóxico (97%) | ✓ |
| 4 | Ya estamos hartos de las mujeres, deberían estar fuera de la terminal asco | Odio | Odio (66%) | ✓ |
| 5 | Pronto le llega su hora a el motorista del bus, lo vamos a buscar a la casa | Amenazas | No Tóxico (66%) | ✗ |
| 6 | Cállate sinvergüenza, nadie te preguntó | Ofensivo | Ofensivo (98%) | ✓ |
| 7 | Eres un estúpido si crees eso de el tráfico | Ofensivo | Ofensivo (98%) | ✓ |
| 8 | Solo las mujeres harían algo tan basura como lo de el tráfico | Odio | Ofensivo (93%) | ✗ |
| 9 | Qué mierda de organización con el tráfico, unos estúpidos | Ofensivo | Ofensivo (98%) | ✓ |
| 10 | Están arruinando todo, esos las mujeres no son de aquí ni valen nada | Odio | Odio (51%) | ✓ |
| 11 | qué payaso tan grande tu opinión sobre el tráfico | Ofensivo | Ofensivo (98%) | ✓ |
| 12 | Ya van a ver, cuando los encuentre en la terminal los mato a todos 💀 | Amenazas | Amenazas (99%) | ✓ |
| 13 | A el motorista del bus hay que colgarlo en la terminal para que aprendan | Amenazas | Amenazas (85%) | ✓ |
| 14 | Hoy en la terminal no se hablaba de otra cosa que de el tráfico | No Tóxico | No Tóxico (88%) | ✓ |
| 15 | No me vengan con las mujeres, esa gente es basura | Odio | Ofensivo (65%) | ✗ |
| 16 | Te voy a descuartizar si no cierras esa boca sobre el tráfico | Amenazas | Amenazas (86%) | ✓ |
| 17 | Ojalá le caiga un rayo a el motorista del bus, que se muera!!! | Amenazas | Amenazas (98%) | ✓ |
| 18 | Qué asco de el tráfico, todo lo hacen mal esos estúpidos | Ofensivo | Ofensivo (97%) | ✓ |
| 19 | No seas sinvergüenza, el tráfico no es tan complicado | Ofensivo | Ofensivo (63%) | ✓ |
| 20 | Hay que quemar la terminal con todos adentro. | Amenazas | Amenazas (97%) | ✓ |

Acierto por tema: Partido de la selección 86%, Mujeres en el trabajo 86%, Tráfico y buses 86%, Elecciones y gobierno 94%, Precio de la canasta 96%, Lluvias e inundaciones 96%, Remesas y migración 96%, Bitcoin y economía 96%, Seguridad y barrios 96%, Concierto y fiestas 98%.
