# Informe de sesgos y ética — modelo v3.3.0

Generado por `src/evaluation/fairness.py` sobre el banco congelado y el test oficial. IC bootstrap 95 % entre corchetes; *sin potencia* = n < 20.

## 0. Resumen global

| Conjunto | n | F1-macro [IC] | Recall NT / OF / OD / AM | FPR (NT) |
|---|---|---|---|---|
| Test oficial | 460 | 0.839 [0.802, 0.873] | 0.89 / 0.82 / 0.78 / 0.88 | 0.114 |
| Banco congelado | 1391 | 0.693 [0.662, 0.722] | 0.87 / 0.80 / 0.58 / 0.49 | 0.129 |

## 1. Por plataforma (test oficial)

| Plataforma | n | F1-macro [IC] | Recall Odio [IC] | Recall Amenazas [IC] | FPR NT [IC] |
|---|---|---|---|---|---|
| Facebook | 232 | 0.764 [0.702, 0.820] | 0.467 [0.286, 0.645] | 0.821 [0.690, 0.938] | 0.093 [0.031, 0.164] |
| X | 228 | 0.880 [0.836, 0.920] | 0.923 [0.846, 0.984] | 0.932 [0.846, 1.000] | 0.146 [0.049, 0.250] |

Brecha de F1-macro entre plataformas: **0.116** (X − Facebook).

## 2. Jerga salvadoreña (test oficial y banco)

| Conjunto | Con jerga / sin jerga | n NT | FPR NT [IC] | n Odio | Recall Odio [IC] |
|---|---|---|---|---|---|
| Test oficial | con jerga | 29 | 0.241 [0.094, 0.412] | 72 | 0.861 [0.767, 0.940] |
| Test oficial | sin jerga | 94 | 0.074 [0.025, 0.137] | 23 | 0.522 [0.312, 0.722] |
| Banco | con jerga | 2 | 0.000 [0.000, 0.000]  *sin potencia* | 4 | 0.500 [0.000, 1.000]  *sin potencia* |
| Banco | sin jerga | 853 | 0.129 [0.106, 0.151] | 126 | 0.579 [0.493, 0.667] |

## 3. Recall de Discurso de Odio por grupo objetivo (test oficial + banco; asignación por palabras clave)

| Grupo objetivo | n Odio | Recall Odio [IC] | Clasificado como Ofensivo | Como No Tóxico |
|---|---|---|---|---|
| LGBT | 13 | 1.000 [1.000, 1.000]  *sin potencia* | 0.00 | 0.00 |
| mujeres/género | 4 | 0.500 [0.000, 1.000]  *sin potencia* | 0.50 | 0.00 |
| etnia/raza | 30 | 0.867 [0.733, 0.967] | 0.03 | 0.07 |
| nacionalidad/migración | 79 | 0.722 [0.620, 0.823] | 0.06 | 0.18 |
| otro | 99 | 0.515 [0.424, 0.606] | 0.23 | 0.22 |

Brecha máxima de recall de Odio entre grupos con n ≥ 20: **0.145** (etnia/raza vs nacionalidad/migración).

## 4. Sobremarcado de menciones: textos **No Tóxico** que mencionan un grupo

| Grupo mencionado | n (NT) | Marcados como tóxicos [IC] |
|---|---|---|
| LGBT | 2 | 0.500 [0.000, 1.000]  *sin potencia* |
| mujeres/género | 13 | 0.154 [0.000, 0.385]  *sin potencia* |
| etnia/raza | 9 | 0.444 [0.111, 0.778]  *sin potencia* |
| nacionalidad/migración | 55 | 0.236 [0.127, 0.345] |

## 5. Por hilo / tema del banco

| Banco | n | Acierto | Recall Odio | Recall Amenazas | FPR NT |
|---|---|---|---|---|---|
| externo2 | 647 | 0.892 | 0.50 | 0.00 | 0.090 |
| migrantes | 306 | 0.784 | 0.52 | 0.33 | 0.190 |
| militares | 202 | 0.663 | 0.00 | 0.48 | 0.119 |
| xenofobia | 236 | 0.661 | 0.61 | 0.71 | 0.324 |

## Límites y advertencias éticas
- Los grupos objetivo se asignan con palabras clave: un texto sobre «mujeres» y «migrantes» cae en el primer grupo que coincide; es aproximado.
- Las etiquetas son consenso de anotadores LLM (Sonnet, Opus y un tercer modelo) **sin validación humana**: el sesgo de esos anotadores puede estar en las etiquetas y en el banco.
- Los datos son de X (salvo la columna de plataforma del test oficial); no se evaluó dialecto individual ni autores.
- El clasificador debe usarse como **apoyo a la moderación con revisión humana**, no como decisión automática: los errores se reparten de forma desigual por grupo (ver tablas) y una sanción errónea tiene costo real para quien la recibe.