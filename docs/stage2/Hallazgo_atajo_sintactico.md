# Hallazgo: el atajo sintáctico «te voy a X»

**Detectado:** 13 de septiembre de 2026, probando el prototipo con la frase
«voy a comer».
**Severidad:** crítica. El modelo publicado clasificaba frases cotidianas
inocuas como Amenazas/Violencia con alta confianza.

---

## Qué pasaba

```
voy a comer                 ->  Amenazas/Violencia   82.6 %
voy a salir                 ->  Amenazas/Violencia   98.7 %
voy a llamar a mi mamá      ->  Amenazas/Violencia   99.7 %
te voy a llamar             ->  Amenazas/Violencia  100.0 %
alguien debería ayudarle    ->  Amenazas/Violencia  100.0 %
hay que llamarlos a todos   ->  Amenazas/Violencia  100.0 %
```

Sobre una sonda de 24 frases inocuas construidas con esas mismas estructuras,
**13 se clasificaban como amenaza**.

## Causa raíz

El modelo no aprendió los verbos violentos: aprendió **la construcción
sintáctica que los envolvía**.

El generador de sintéticos usa una lista de portadores —«Te voy a {verbo}»,
«Hay que {verbo}los a todos», «Alguien debería {verbo} a ese tipo»— y los
rellena únicamente con verbos de agresión. El resultado es que esas
construcciones aparecen en el entrenamiento casi solo con la etiqueta Amenaza, y
**nunca con la etiqueta No Tóxico**:

| Corpus | Filas con «te voy a» | De ellas, Amenaza | Origen sintético |
|---|---|---|---|
| train v1 (Etapa I) | 3 | 1 (33 %) | 0 |
| train B2 (agosto) | 29 | 27 (93 %) | 26 |
| train V3 (antes del arreglo) | 47 | 45 (96 %) | 44 |

Sin un solo contraejemplo, el atajo es la solución más barata que el modelo
puede encontrar, y la toma.

La comparación entre modelos confirma que el defecto entra con los sintéticos y
se agrava con cada ampliación. Probabilidad media de Amenaza sobre siete frases
inocuas:

| Modelo | Sintéticos de plantilla | p(amenaza) media |
|---|---|---|
| XLM-R v1 (Etapa I) | ninguno | **14.6 %** |
| mBERT v1 (Etapa I) | ninguno | 35.7 % |
| TwitterXLM-R sobre B2 | 1,149 | 67.4 % |
| mBERT B2 | 1,149 | 80.7 % |
| V3 antes del arreglo | 4,058 | **82.6 %** |

Es el mismo fallo que la auditoría documentó con los emojis en la v1 —«hay
emoji, es ofensivo»— trasladado a una construcción sintáctica. El generador ya
llevaba pares mínimos para la jerga y para los emojis; **no se los puse a los
portadores de amenaza.**

## Por qué no lo detectó ninguna métrica

Las construcciones afectadas aparecen en **14 de las 460 instancias del conjunto
de prueba (3 %)**. Un modelo puede tener el atajo completamente instalado y no
perder casi nada de F1-macro, porque el test no ejercita esa zona.

Ni la batería adversarial de 144 casos ni la sonda dirigida de 204 lo cubrían:
ambas fueron diseñadas contra la ofuscación, los emojis y el sesgo dialectal, y
ninguna incluye la construcción de amenaza rellenada con un verbo inocuo.

**Es la lección metodológica del hallazgo:** una métrica agregada sobre un test
que no muestrea el modo de fallo no lo ve, por alta que sea.

## Corrección

Se añade al generador la familia `v3_amenaza_control`: los mismos portadores de
amenaza, sin tocarlos, rellenados con quince verbos inocuos que admiten la misma
morfología (`llamar`, `invitar`, `ayudar`, `esperar`, `visitar`, `saludar`,
`acompañar`, `felicitar`…), etiquetados **No Tóxico**. Son 219 filas.

Se excluye el verbo `buscar` a propósito: «te voy a buscar» sí se usa como
amenaza y la batería adversarial lo tiene etiquetado así; enseñarlo como inocuo
introduciría una contradicción en el corpus.

Se excluyen también dos portadores que no admiten lectura inocua bajo ningún
verbo («No respondo si lo llego a…», «Si lo vuelvo a ver lo voy a…»).

Tras la corrección, «te voy a» pasa de 96 % a 75 % de etiqueta Amenaza, con 14
ejemplos No Tóxico donde antes había cero.

## Efecto de la corrección

| | Antes | Después |
|---|---|---|
| Falsos positivos en la sonda de construcción | **13 / 24** | **1 / 24** |
| p(amenaza) media en frases inocuas | 53.2 % | **3.7 %** |
| p(amenaza) media en amenazas reales | 100 % | **100 %** |
| Separación entre ambas | +46.8 % | **+96.3 %** |
| Batería adversarial (144) | 125 | **129** |
| Sonda dirigida (204) | 200 | **201** |
| FPR con jerga sobre el test real | 0.2759 | **0.2414** |
| **F1-macro sobre el test** | **0.8499** | **0.8287** |
| IC 95 % inferior | 0.8164 | 0.7918 |

No se perdió ni una amenaza real: las diez de la sonda siguen detectándose al
100 %.

## Resultado final tras reoptimizar

Los hiperparámetros en uso se habían buscado sobre el corpus anterior, con 214
filas menos y otra distribución de clases, así que se rehízo la búsqueda sobre
el corpus corregido (veinte pruebas, sobre validación, sin tocar el test).

| Sistema | F1 test | IC 95 % inferior | Falsos positivos en la sonda |
|---|---|---|---|
| Antes del arreglo (publicado) | 0.8499 | 0.8164 | **13 / 24** |
| Modelo individual corregido | 0.8268 | 0.7912 | **0 / 24** |
| **Ensemble de las tres semillas corregidas** | **0.8529** | **0.8191** | **0 / 24** |
| Ensemble incluyendo TwitterXLM-R sobre B2 | 0.8495 | 0.8148 | 2 / 24 |

El ensemble de las tres semillas corregidas recupera la meta —el extremo
inferior del intervalo queda en 0.8191— **y mantiene el atajo eliminado**.

Se excluyó a propósito al TwitterXLM-R entrenado sobre B2, aunque estaba en el
ensemble anterior: arrastra el atajo con 14 falsos positivos de 24 y lo
reintroduce en el promedio. Un miembro con un defecto conocido contamina el
conjunto aunque suba la métrica agregada.

**Regla de selección, fijada antes de mirar el test:** se promedian las tres
semillas, sin elegir ninguna. El mejor modelo individual sobre validación es la
semilla 2026 (0.8562), pero esa semilla conserva 4 falsos positivos de 24 en la
sonda; escogerla habría sido seleccionar por la métrica que no ve el defecto.

Un dato que conviene declarar: la dispersión entre semillas en la sonda es alta
—0, 0 y 4 falsos positivos— lo que indica que el contrapeso corrige el atajo
pero no de forma uniforme. Con 219 ejemplos de contrapeso frente a 2,144 reales,
la señal existe pero es frágil.

## La lectura honesta

Con los hiperparámetros anteriores la corrección costaba 0.021 de F1-macro y
dejaba el intervalo por debajo de la meta. Tras reoptimizar y promediar las tres
semillas, el sistema corregido **supera al anterior** (0.8529 frente a 0.8499) y
además no tiene el atajo.

Conviene ser explícito sobre qué significa eso. El 0.8499 se apoyaba en parte en
un modelo que llamaba amenaza a «voy a comer». Un sistema así no es mejor: es
uno cuyo modo de fallo el conjunto de prueba no muestrea. Presentar esa cifra
sabiendo lo que ahora sabemos sería exactamente el tipo de defensa que este
mismo proyecto auditó y rechazó en la entrega anterior.

Que la cifra final haya subido no debe leerse como que el problema no existía.
El 0.8499 anterior se apoyaba en parte en un modelo que llamaba amenaza a «voy a
comer»; que el conjunto de prueba no lo penalizara es un defecto del conjunto de
prueba, no una virtud del modelo.

## Qué se agrega al conjunto de pruebas

`src/v3/sonda_construccion.py`: 24 frases inocuas y 10 amenazas reales que
comparten portador. Se ejecuta tras cada reentrenamiento. El diseño del generador
tiene ahora tres pares mínimos —emoji, jerga y construcción de amenaza— y la
regla general que se deriva de los tres es:

> Toda estructura que el generador use para producir una clase debe aparecer
> también, con relleno distinto, produciendo otra. Si no, el modelo aprende la
> estructura.
