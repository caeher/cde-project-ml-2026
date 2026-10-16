# Reentrenamiento v4 — resultado (7 de octubre de 2026)

Mismo código (`src/train/entrenar_v4.py`), mismo archivo (`data/history/v1.3.1/train.csv`), mismas semillas (42, 1337, 2026), RTX 4060 local. Única diferencia: `--peso_nuevos` (1.0 con octubre, 0.0 línea base de 6,395 filas). Cifras recalculadas por `src/evaluation/comparar_v4.py` (detalle en `runs/comparacion.json`).

| | Base (sin octubre) | v4 (con octubre) |
|---|---|---|
| F1-macro test (ensemble) | 0.8358 [0.7994, 0.8693] | 0.8340 [0.7980, 0.8673] |
| Aciertos / 460 | 386 | 385 |
| Semillas sueltas (media ± de) | 0.8241 ± 0.0084 | 0.8260 ± 0.0184 |
| Δ F1 (v4 − base) | | −0.0018, IC pareado [−0.0269, +0.0241] |
| McNemar | b = 15, c = 16, p = 1.00 | |
| X (n=228) | 0.8964 | 0.9048 (Δ +0.008, p = 0.73) |
| Facebook (n=232) | 0.7348 | 0.7223 (Δ −0.013, p = 0.68) |
| FPR sin jerga | 9/94 = 0.096 | 15/94 = 0.160 |
| FPR con jerga (n=29, sin potencia) | 0.310 | 0.310 |
| Batería 144 | 122 | 126 (p = 0.22) |
| F1 val (ensemble) | 0.8537 | 0.8365 |

## Conclusión
- **No hay mejora demostrable.** El Δ es −0.002 y el IC cruza el cero; McNemar no distingue los modelos. Tampoco hay empeoramiento demostrable.
- El extremo inferior del IC es < 0.80 en ambos (0.7994 y 0.7980): la meta «con el IC» no se cumple con esta corrida, ni siquiera en la línea base.
- Los datos de octubre repiten el patrón del proxy lineal (X sube, Facebook baja), pero ninguna diferencia es significativa.
- FPR sin jerga empeora de 9.6 % a 16.0 % con v4 (no se probó su significancia).
- **Decisión sugerida: no adoptar v4.** Con val como criterio (fijado de antemano), la base gana (0.8537 vs 0.8365).

## Reproducción de la Etapa II
La línea base reproduce 0.8358, no 0.8529 (informado por la Etapa II). La diferencia (−1.7 puntos) es del tamaño de la dispersión entre semillas (de ≈ 1.8) y la base usa 6,395 filas en vez de 6,416, pero no se midió si explica toda la diferencia. Conviene decirlo en la tesina.

## Exploratorio (no usar para decidir)
Promediar las 6 semillas da test 0.8482 (392/460), pero en val da 0.8502 < 0.8537 de la base sola. Mirar test para elegir sería usar el test para seleccionar; queda como observación.

## Variantes probadas después (selección por val)

Se probaron dos variantes de v4 con el mismo código y semillas. Criterio fijado antes de mirar test: elegir el mayor F1 en val.

| Corrida | F1 val | F1 test | IC 95 % test | Δ vs base [IC pareado] | McNemar p | Facebook Δ | FPR sin jerga |
|---|---|---|---|---|---|---|---|
| base | **0.8537** | 0.8358 | [0.7994, 0.8693] | | | | 0.096 |
| v4 (peso 1.0) | 0.8365 | 0.8340 | [0.7980, 0.8673] | −0.002 [−0.027, +0.024] | 1.00 | −0.013 | 0.160 |
| v4_p03 (peso 0.3) | 0.8517 | 0.8390* | [0.8041, 0.8727] | +0.003 [−0.021, +0.028] | 0.85 | +0.022 | 0.128 |
| v4_p03_sv (peso 0.3, sin fuera de SV) | 0.8437 | 0.8308* | [0.7944, 0.8643] | −0.005 [−0.029, +0.020] | 0.86 | +0.012 | 0.138 |

\* F1 de test leído de la comparación pareada; no entró en la selección.

**Conclusión final:** por val gana la base; ninguna variante supera a la base con significancia (todos los IC del Δ cruzan el cero, p ≥ 0.85). v4_p03 es la única con extremo inferior ≥ 0.80 (0.8041), pero eso es una diferencia de 0.005 entre dos IC que se solapan casi por completo, tras probar tres variantes: no es evidencia de mejora. Con n = 460 esta comparación no puede detectar diferencias de 1 punto.

La mejora que el proyecto necesita no sale de más X: hace falta Facebook, sarcasmo/ironía, validación de etiquetas con segundo anotador y un test más grande.

## Calibración (pendiente 7 del review) — `src/evaluation/calibracion.py`

Temperature scaling del ensemble, T ajustada solo en val (no cambia ninguna predicción: el argmax es idéntico).

| Modelo | T | ECE test antes → después | NLL test antes → después |
|---|---|---|---|
| base | 1.213 | 0.0486 → **0.0199** | 0.4614 → 0.4479 |
| v4_p03 | 2.458 | 0.1028 → 0.0207 | 0.7676 → 0.4769 |

El ECE de la base ya era 0.049 antes de escalar, frente al 0.1214 informado en la Etapa II. No se comparó el método de binning de aquel reporte (aquí 10 bins de igual ancho), así que no es una mejora demostrada sobre esa cifra. Con T = 1.213 el modelo queda mejor calibrado sin tocar las predicciones. Ese ajuste es una mejora real y medida, aunque no del F1.

## Estado final (provisional; ver «Estado final vigente» al pie)
Esta sección refleja el momento previo a la base de 5 semillas y quedó superada por las secciones posteriores.

## Base con 5 semillas (42, 1337, 2026, 7, 99) — `runs/base5`

Mismo código y receta, sin octubre; se añadieron dos semillas a la base. Criterio fijado antes: adoptar solo si mejora el F1 en val.

| | base (3 sem.) | **base5 (5 sem.)** |
|---|---|---|
| F1 val | 0.8537 | **0.8621** |
| F1 test | 0.8358 | **0.8499** |
| IC 95 % test | [0.7994, 0.8693] | **[0.8143, 0.8820]** |
| Extremo inferior ≥ 0.80 | NO | **sí** |
| Δ test vs base 3 sem. | | +0.014, IC pareado [−0.003, +0.033] |
| McNemar | | b/c = 11/5, p = 0.21 |
| Facebook | 0.7348 | 0.7686 (Δ +0.034, p = 0.34) |
| FPR sin jerga | 0.096 | 0.096 |
| ECE test con T = 1.349 | | 0.0561 → 0.0271 |

**Lectura:** gana en val, que era el criterio fijado, y es el único modelo de esta tanda que cumple la meta (extremo inferior del IC 0.8143 ≥ 0.80). Frente a la base de 3 semillas la diferencia **no es significativa** (p = 0.21; el IC del Δ cruza el cero): el aumento viene de reducir la varianza del ensemble, no de un modelo distinto. La meta del proyecto se cumple con esta configuración; la «mejora» sobre la base es un punto estimado, no una demostración.

**Modelo final recomendado:** RoBERTuito, 5 semillas, sin datos de octubre (el v4 con octubre no aportó), con temperature scaling T = 1.349.

## Alcance acordado (7 de octubre)
- **No se recolectarán más datos de Facebook.** La debilidad en Facebook (F1 0.7686 en test, frente a 0.9041 en X) queda como **limitación conocida**, a reportar en la tesina con su IC y el χ² de domain shift (V de Cramér 0.216).
- **Las clases son solo 4** (No Tóxico, Ofensivo, Odio, Amenazas). «Sarcasmo» e «ironía» no son clases: son las anotaciones `Presencia_Sarcasmo` / `Presencia_Ironia`, usadas solo como cortes de análisis de errores (F1 ≈ 0.66 y 0.59 en esos cortes). También son limitación conocida, no tarea pendiente.
- Pendientes que sí quedan: segundo anotador sobre una muestra de octubre (solo si se quiere usar esos datos; el modelo final no los usa), test ampliado (opcional) y pegar `docs/stage2/Fe_de_erratas_EtapaII.md` en el reporte del repo del equipo.

## Sistema final frente a los modelos de la Etapa I

Pareado sobre el mismo test (n = 460), predicciones recalculadas del modelo final guardado (`models/v3.0.0`) contra `reports/stage2/preds_xlmr.csv` (XLM-R v1; `reports/stage2/preds_test.csv` es el mismo modelo, F1 0.8058).

| | XLM-R v1 | Final (5 semillas) |
|---|---|---|
| F1-macro test | 0.8058 | **0.8499** |
| Δ | | **+0.0441**, IC pareado [+0.0138, +0.0745] |
| McNemar | | solo final acierta 37 · solo XLM-R acierta 16 · **p = 0.0055** |

**Esta sí es una mejora demostrable:** el IC del Δ no cruza el cero y McNemar es significativo (α = 0.05). XLM-R v1 era el mejor de la Etapa I; mBERT v1 (0.7777) quedó por debajo, aunque no se re-comparó porque sus predicciones no están en esta carpeta (según la verificación del 1 de septiembre, McNemar entre ambos de la Etapa I dio p = 0.20: empate).

La mejora entre la Etapa II publicada (0.8529) y este cierre no es demostrable, ni a favor ni en contra: la diferencia (−0.003) está dentro del ruido, y la línea base reproducida de 3 semillas dio 0.8358.

## Estado final vigente (10 de octubre de 2026)
- **Modelo final:** RoBERTuito, 5 semillas, sin octubre, temperature scaling T = 1.349 (`models/v3.0.0`). F1-macro test 0.8499, IC [0.8143, 0.8820]: la meta se cumple con el IC completo.
- **Mejora demostrada:** frente a XLM-R v1 (Etapa I), Δ +0.0441, p = 0.0055. No demostrable frente a la base de 3 semillas (p = 0.21) ni frente al 0.8529 de la Etapa II (−0.003).
- **Limitaciones conocidas (sin recolección adicional):** Facebook (0.7686 frente a 0.9041 en X) y cortes con sarcasmo/ironía.
- **Prototipo:** `app/api/main.py` y `app/ui/app.py`; la API reproduce 0.8499 en test.
- **Pendiente externo:** aplicar `docs/stage2/Fe_de_erratas_EtapaII.md` al reporte de la Etapa II (repo del equipo, rama v3) y recalcular allí las cifras de los puntos 3, 5 y 6.

## Modelo v5: hilos reales + casos difíciles (11–14 de octubre de 2026)
Detalle de la estrategia y los criterios: `docs/improvement/Estrategia_mejora.md`. Misma receta que `models/v3.0.0` (RoBERTuito, 5 semillas, mismas semillas), añadiendo 716 respuestas reales de 4 hilos de X (etiquetadas con la guía v2.0, sin segundo anotador) y 88 pares mínimos escritos a mano, con peso 1.0. Modelo final: `models/v3.1.0`, T = 1.832 (ajustada en val).

| Medida | `final5` (anterior) | `final_v5` (nuevo) |
|---|---|---|
| Test oficial, F1-macro | 0.8499 | 0.8327 (Δ −0.017, IC [−0.042, +0.006], McNemar p = 0.136) |
| Batería de 144 | 127 | 129 |
| ECE en test tras escalar | 0.0271 | 0.0215 |
| Hilos reservados (canje + feminismo, validación del diseño con modelo entrenado solo con otros 2 hilos), F1-macro | 0.415 | 0.528 (Δ +0.113, IC [+0.067, +0.165], p < 0.0001) |
| **Hilo nuevo CECOT (n = 209), F1-macro** | 0.470 | **0.613** (Δ +0.144, IC pareado [+0.070, +0.220], McNemar b/c 42/8, p < 0.0001) |
| CECOT: acierto | 56.5 % | 72.7 % |
| CECOT: recall No Tóxico (falsos positivos) | 0.517 | 0.783 |
| CECOT: recall Amenazas | 0.640 | 0.600 |

**Prueba de atajos** (`src/evaluation/prueba_atajos.py`, invariancia contrafactual): ataque a 8 grupos → Odio 1.00 en todos (antes 0.80 para «mujeres»); mención neutra de grupo → No Tóxico 0.97; amenaza explícita y neutro en 8 temas 1.00; emoji inocuo 1.00; palabra gatillo inocua 1.00. Solape de 4-gramas con lo añadido al train: 2.6 % de los textos reservados, con igual acierto con y sin solape.

**Lectura honesta**
- Mejora grande y significativa en hilos reales (dos mediciones: hilos reservados y un hilo completamente nuevo), sobre todo menos falsos positivos sobre No Tóxico.
- Costo: −0.017 de F1 en el test oficial (no significativo, pero el IC casi toca +0.006). Se adoptó con el criterio revisado y autorizado por la persona responsable (sin regresión significativa).
- No mejoró: recall de Amenazas en CECOT (0.64 → 0.60), Odio sigue bajo en hilos reservados (0.088 → 0.147), amenazas implícitas en los casos de prueba (0.75 → 0.75).
- Etiquetas de los hilos: una sola anotadora, guía v2.0, **sin validar por humano**. La convención de la guía para discurso punitivo contra pandillas («escoria», «que se pudran» → Amenazas) es estricta y condiciona los números de la clase Amenazas.
- Se probaron 2 pesos (3.0 y 1.0); el 3.0 falló. El resultado del 1.0 es algo optimista por esa elección.

## Renombrado de versiones y candidato v3.2.0-rc1 (14 de octubre de 2026)
Ver `CHANGELOG.md`. `final5` = **v3.0.0**, `final_v5` = **v3.1.0** (en la API), `final_v6` = **v3.2.0-rc1** (candidato, no adoptado).

**Etiquetado por consenso.** Mis 1,155 etiquetas de 6 hilos se compararon con las de agentes independientes y ciegos: κ = 0.77 (κ = 0.96 donde el agente estaba seguro); entre dos agentes sobre el hilo de migrantes κ = 0.90 y sobre 3 hilos nuevos κ = 0.80. El consenso (mayoría de 3) cambió 125 de mis 1,155 etiquetas, sobre todo de No Tóxico a Ofensivo (fui más permisiva con insultos leves). Sin mayoría el texto se excluye (11 de 1,999).

**Re-medición con consenso (hilos CECOT + Miss, ninguno visto por v3.0.0 ni v3.1.0; n = 439):** F1-macro 0.526 → 0.623 (Δ +0.097, IC [+0.051, +0.144], McNemar b/c 83/21, p < 0.0001). La mejora de v3.1.0 sobre v3.0.0 no depende de mi sesgo de etiquetado. Recall No Tóxico 0.474 → 0.741; Amenazas 0.618 → 0.564.

**Hilo externo de migrantes (n = 307, consenso, nunca entrenado):** v3.0.0 F1 0.504 · v3.1.0 0.590 · v3.2.0-rc1 0.634.

**Candidato v3.2.0-rc1 frente a v3.1.0** (`comparar_candidato.py`): test oficial 0.8327 → 0.8388 (p = 0.73); batería 129 → 130; migrantes F1 0.590 → 0.634 (Δ +0.044, IC [−0.011, +0.108], p = 0.053) → criterio (c) no cumplido; vulgaridad afectiva 19/20 y 18/18. **No adoptado** por la regla fijada de antemano; recall de Odio en migrantes 0.576 → 0.515 (n = 33).

## Combinación de modelos y v3.2.0 (14 de octubre de 2026)
Ver `CHANGELOG.md` §v3.2.0 y `reports/improvement/combinacion_modelos.json`. Resumen: los 4 modelos públicos de odio/toxicidad en español no mejoran al propio ni solos ni combinados (stacking Δ ≈ 0 o negativo); promediar v3.1.0 con v3.2.0-rc1 (10 modelos) cumple los tres criterios fijados de antemano (agrupado Δ +0.033, IC [+0.009, +0.059]; test oficial 0.8429; afectivas 19/20) y pasa a ser **v3.2.0**, el modelo de la API.

## Amenazas y candidato v3.3.0-rc1 (14 de octubre de 2026)
Test externo 3 (590 textos, 3 hilos sobre pandilleros/CECOT; consenso, κ = 0.88; 173 de Amenazas): recall de Amenazas v3.0.0 0.474 · v3.1.0 0.382 · v3.2.0-rc1 0.451 · v3.2.0 0.428; FPR sobre No Tóxico 28.2 % → 15.0 % → 14.7 % → 14.0 %; v3.2.0 mejora a v3.1.0 (ΔF1 +0.026, IC [+0.007, +0.046], McNemar p = 0.0125). v3.3.0-rc1 (entrenado con 2 de esos 3 hilos) llega a F1-Amenazas 0.643 vs 0.579 en el hilo reservado (IC Δ [+0.011, +0.120]) sin subir falsos positivos, pero pierde 3 aciertos netos en la batería (criterio b) y **no se adopta**. Ver `CHANGELOG.md`.

## v3.3.0 en la API (14 de octubre de 2026)
Promovido por decisión de la persona responsable: ensamble v3.2.0-rc1 + v3.3.0-rc1 (10 modelos, T = 1.314). Frente a v3.2.0: test oficial 0.8429 → 0.8386 (p = 0.815), batería 129 → 129, F1 de Amenazas en hilo reservado 0.575 → 0.618, FPR 12.2 % → 10.9 %. Detalle y límites en `CHANGELOG.md`.
