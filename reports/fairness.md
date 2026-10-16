# Informe de sesgos y ética — modelo v3.4.0

Generado por `src/evaluation/fairness.py` sobre el banco congelado y el test oficial. IC bootstrap 95 % entre corchetes; *sin potencia* = n < 20.

## 0. Resumen global

| Conjunto | n | F1-macro [IC] | Recall NT / OF / OD / AM | FPR (NT) |
|---|---|---|---|---|
| Test oficial | 460 | 0.832 [0.795, 0.864] | 0.85 / 0.81 / 0.82 / 0.86 | 0.146 |
| Banco congelado | 1391 | 0.720 [0.688, 0.753] | 0.89 / 0.81 / 0.67 / 0.47 | 0.112 |

## 1. Por plataforma (test oficial)

| Plataforma | n | F1-macro [IC] | Recall Odio [IC] | Recall Amenazas [IC] | FPR NT [IC] |
|---|---|---|---|---|---|
| Facebook | 232 | 0.761 [0.697, 0.820] | 0.533 [0.350, 0.720] | 0.795 [0.659, 0.913] | 0.107 [0.039, 0.182] |
| X | 228 | 0.865 [0.817, 0.907] | 0.954 [0.896, 1.000] | 0.909 [0.814, 0.979] | 0.208 [0.095, 0.327] |

Brecha de F1-macro entre plataformas: **0.103** (X − Facebook).

## 2. Jerga salvadoreña (test oficial y banco)

| Conjunto | Con jerga / sin jerga | n NT | FPR NT [IC] | n Odio | Recall Odio [IC] |
|---|---|---|---|---|---|
| Test oficial | con jerga | 29 | 0.379 [0.207, 0.565] | 72 | 0.931 [0.868, 0.986] |
| Test oficial | sin jerga | 94 | 0.074 [0.030, 0.135] | 23 | 0.478 [0.278, 0.692] |
| Banco | con jerga | 2 | 0.000 [0.000, 0.000]  *sin potencia* | 4 | 0.500 [0.000, 1.000]  *sin potencia* |
| Banco | sin jerga | 853 | 0.113 [0.092, 0.135] | 126 | 0.675 [0.588, 0.755] |

## 3. Recall de Discurso de Odio por grupo objetivo (test oficial + banco; asignación por palabras clave)

| Grupo objetivo | n Odio | Recall Odio [IC] | Clasificado como Ofensivo | Como No Tóxico |
|---|---|---|---|---|
| LGBT | 13 | 0.923 [0.769, 1.000]  *sin potencia* | 0.00 | 0.08 |
| mujeres/género | 4 | 0.500 [0.000, 1.000]  *sin potencia* | 0.50 | 0.00 |
| etnia/raza | 30 | 0.900 [0.767, 1.000] | 0.03 | 0.03 |
| nacionalidad/migración | 79 | 0.810 [0.722, 0.899] | 0.03 | 0.14 |
| otro | 99 | 0.606 [0.515, 0.697] | 0.18 | 0.20 |

Brecha máxima de recall de Odio entre grupos con n ≥ 20: **0.090** (etnia/raza vs nacionalidad/migración).

## 4. Sobremarcado de menciones: textos **No Tóxico** que mencionan un grupo

| Grupo mencionado | n (NT) | Marcados como tóxicos [IC] |
|---|---|---|
| LGBT | 2 | 1.000 [1.000, 1.000]  *sin potencia* |
| mujeres/género | 13 | 0.385 [0.154, 0.692]  *sin potencia* |
| etnia/raza | 9 | 0.667 [0.333, 0.889]  *sin potencia* |
| nacionalidad/migración | 55 | 0.218 [0.109, 0.327] |

## 5. Por hilo / tema del banco

| Banco | n | Acierto | Recall Odio | Recall Amenazas | FPR NT |
|---|---|---|---|---|---|
| externo2 | 647 | 0.881 | 0.50 | 0.00 | 0.099 |
| migrantes | 306 | 0.846 | 0.73 | 0.00 | 0.134 |
| militares | 202 | 0.673 | 0.00 | 0.48 | 0.095 |
| xenofobia | 236 | 0.725 | 0.66 | 0.57 | 0.197 |

## Límites y advertencias éticas
- Los grupos objetivo se asignan con palabras clave: un texto sobre «mujeres» y «migrantes» cae en el primer grupo que coincide; es aproximado.
- Las etiquetas son consenso de anotadores LLM (Sonnet, Opus y un tercer modelo) **sin validación humana**: el sesgo de esos anotadores puede estar en las etiquetas y en el banco.
- Los datos son de X (salvo la columna de plataforma del test oficial); no se evaluó dialecto individual ni autores.
- El clasificador debe usarse como **apoyo a la moderación con revisión humana**, no como decisión automática: los errores se reparten de forma desigual por grupo (ver tablas) y una sanción errónea tiene costo real para quien la recibe.