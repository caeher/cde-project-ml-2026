# Versiones del modelo

Numeración semántica sobre la rama v3 (Etapa II). Pesos en `models/<versión>/` (no versionados en git).

| Versión | Antes se llamaba | Qué es | F1-macro test oficial | Estado |
|---|---|---|---|---|
| **v3.0.0** | `final5` | RoBERTuito, 5 semillas, sin datos de octubre. T = 1.349 | 0.8499 | anterior |
| v3.1.0 | `final_v5` | v3.0.0 + 716 respuestas de 4 hilos reales (etiquetas de Claude) + 88 casos difíciles. T = 1.832 | 0.8327 | componente de v3.2.0 |
| v3.2.0-rc1 | `final_v6` | v3.1.0 pero con etiquetas de **consenso de 3 anotadores** y 9 hilos (1,681 filas; 232 de Odio) | 0.8388 | componente de v3.2.0 (solo no se adopta) |
| v3.2.0 | — | Ensamble de 10 modelos: promedio de probabilidades de v3.1.0 + v3.2.0-rc1. T = 1.619 | 0.8429 | anterior |
| v3.3.0 | — | Ensamble de 10 modelos: v3.2.0-rc1 + v3.3.0-rc1 (este con hilos ricos en Amenazas). T = 1.314 (ajustada en val) | 0.8386 | anterior (rollback: `MODELOS` en `app/api/main.py`) |
| **v3.4.0** | — | **UN solo RoBERTuito** destilado del ensamble `candC` (A+B, 6 modelos) con la receta de Optuna; datos: `dataset_final` (12,641 filas). T = 1.582 (val) | **0.8317** | **en la API** |

## Por qué v3.2.0-rc1 no se adoptó
Criterios fijados antes de ver resultados (`src/evaluation/comparar_candidato.py`), referencia v3.1.0:
(a) test oficial sin regresión significativa: **sí** (Δ +0.006, p = 0.73) · (b) batería no baja más de 2: **sí** (129 → 130) ·
(c) mejora en hilo externo de migrantes (nunca entrenado) con IC que no cruza cero: **NO** (F1 0.590 → 0.634, Δ +0.044, IC [−0.011, +0.108], p = 0.053) ·
(d) vulgaridad afectiva salvadoreña: **sí** (19/20 afectivas, 18/18 insultos).
Es un resultado de frontera, no un fracaso: mejora todos los puntos estimados salvo el recall de Odio en migrantes (0.576 → 0.515, n = 33).
Para promoverlo a v3.2.0 haría falta cumplir (c) con más datos de test externo, o una decisión explícita de la persona responsable de relajar el criterio.

## Datasets (sin renombrar)
`dataset_v4` (Etapa II + octubre), `dataset_v5a` (experimento con hilos reservados), `dataset_v5f` (entrena v3.1.0), `dataset_v6` (entrena v3.2.0-rc1).

## v3.2.0 — ensamble (14 de octubre de 2026)
Se evaluaron combinaciones con criterio fijado antes de ver resultados (`src/evaluation/combinar_modelos.py`, referencia v3.1.0 solo):
(1) F1-macro agrupado en migrantes (307) + externo 2 (650: fútbol, política y seguridad en El Salvador) mejora con IC pareado > 0; (2) test oficial sin regresión significativa; (3) vulgaridad afectiva ≥ 17/20 e insultos ≥ 16/18.

| Combinación | Test oficial | Migrantes | Externo 2 | Agrupado Δ [IC 95 %] | Criterios |
|---|---|---|---|---|---|
| v3.1.0 solo (referencia) | 0.8327 | 0.5904 | 0.4597 | — | — |
| + robertuito-hate-speech (stacking) | 0.8323 | 0.5994 | 0.4029 | +0.002 [−0.037, +0.038] | no |
| + 4 modelos públicos (stacking) | 0.8182 | 0.5741 | 0.4000 | −0.011 [−0.051, +0.027] | no |
| solo los 4 públicos | 0.4954 | 0.5217 | 0.3872 | −0.071 [−0.127, −0.012] | no |
| promedio v3.0.0 + v3.1.0 + v3.2.0-rc1 | 0.8508 | 0.6026 | 0.4446 | −0.005 [−0.033, +0.022] | no |
| **promedio v3.1.0 + v3.2.0-rc1 = v3.2.0** | **0.8429** | **0.6376** | **0.4711** | **+0.033 [+0.009, +0.059]** | **sí (1, 2 y 3)** |

Los modelos públicos (`pysentimiento/robertuito-hate-speech`, `Hate-speech-CNERG/dehatebert-mono-spanish`, `JonatanGk/roberta-base-bne-finetuned-hate-speech-offensive-spanish`, `bgonzalezbustamante/bert-spanish-toxicity`) son bastante peores solos (AUROC tóxico 0.68–0.85 frente a 0.95 del propio) y no aportan al combinarlos. El de toxicidad marca como tóxicas las groserías afectivas salvadoreñas (solo 6/20 afectivas bien). Argilla no publica un modelo de odio en español (sus modelos son de recompensa y de dominios); su rol aquí lo cumplió el etiquetado por consenso de anotadores independientes.

Detalle v3.2.0: migrantes acierto 0.808 y recall de Odio 0.606 (v3.1.0: 0.752 / 0.576; rc1: 0.795 / 0.515); externo 2 acierto 0.889; batería 129; ECE test 0.068 → 0.032 con T; atajos 1.00 en las 6 familias; vulgaridad afectiva 19/20 y 18/18.

**Límites:** se compararon 6 combinaciones (algo optimista); el hilo de migrantes ya se había usado para juzgar rc1; el externo 2 casi no tiene Odio ni Amenazas (2 y 1 textos), por lo que su F1-macro es ruidoso y solo sirve su acierto; las etiquetas son de consenso de agentes, sin validación humana. Costo: 10 modelos, ≈ 2× la latencia y la memoria de v3.1.0.

## v3.3.0-rc1 — componente de v3.3.0 (14 de octubre de 2026)
Misma receta que v3.2.0-rc1 más 2 hilos ricos en Amenazas (infierno_tierra, pandilleros_traslado: 387 textos, 66 de Amenazas; consenso de 3 anotadores). Reservado entero: `militares_pandilleros` (203 textos, 107 Amenazas). Criterios fijados antes de ver resultados (`src/evaluation/comparar_v330.py`, referencia v3.2.0-rc1):

| Criterio | Resultado |
|---|---|
| (a) test oficial sin regresión | **sí** (0.8388 → 0.8392, p = 1.0) |
| (b) batería no pierde más de 2 | **NO** (130 → 127; pierde 4, gana 1) |
| (c) F1 de Amenazas en hilo reservado, IC > 0 | **sí** (0.579 → 0.643, Δ IC [+0.011, +0.120]; recall 0.430 → 0.514) |
| (d) vulgaridad afectiva | **sí** (19/20 y 18/18) |
| (e) falsos positivos sin subir > 0.03 | **sí** (0.111 → 0.105) |

Es un resultado de frontera: 4 de 5 criterios, y mejora la clase más débil sin costo en falsos positivos. No se adopta por la regla fijada. Las 4 pérdidas de la batería: «Qué verga, ni me acordaba de la reunión» (afectiva sin destinatario → Ofensivo) y dos ataques cuyo vehículo es un emoji (🐷, 🌑) que pasan a No Tóxico, más «No lo quiero ver más por aquí». Para promoverlo: confirmar con más datos o decisión explícita de la persona responsable. Un ensamble de los tres grupos (15 modelos) cabría mal en una GPU de 8 GB.

## Estado de Amenazas (clase más débil)
En 590 textos de hilos sobre pandilleros/CECOT (173 de Amenazas), ningún modelo supera 0.47 de recall (v3.0.0 0.474 · v3.1.0 0.382 · v3.2.0-rc1 0.451 · **v3.2.0 0.428**). Son frases como «que se pudran» o «escoria» que la guía clasifica como Amenazas y los modelos tratan como opinión. v3.3.0-rc1 llega a 0.514 en un hilo reservado.

## v3.3.0 — promovido por decisión de la persona responsable (14 de octubre de 2026)
v3.3.0-rc1 fallaba el criterio (b) de la batería por 1 caso (130 → 127; límite 2). La persona responsable autorizó promoverlo («dale hazlo»). Evidencia que acompaña la decisión:
- La pérdida de batería **no es distinguible del ruido**: McNemar p = 0.375 (solo cand acierta 1, solo ref acierta 4); una sola semilla varía hasta 8 aciertos (v3.1.0: 122–130); quitar 1 de 5 semillas de v3.2.0-rc1 mueve la batería de 128 a 131.
- Se desplegó como ensamble del mismo tamaño que v3.2.0 (10 modelos), sustituyendo a v3.1.0 por v3.3.0-rc1, para no aumentar memoria ni latencia. Resultado del ensamble frente a v3.2.0:

| | v3.2.0 | **v3.3.0** |
|---|---|---|
| Test oficial, F1-macro | 0.8429 | 0.8386 (McNemar b/c 8/10, p = 0.815: sin regresión significativa) |
| Batería de 144 | 129 | **129** (sin pérdida) |
| Hilo reservado `militares_pandilleros`: F1 de Amenazas | 0.575 | **0.618** |
| Recall de Amenazas en ese hilo | 0.430 | **0.477** |
| Acierto en ese hilo (McNemar b/c 9/3) | 0.631 | 0.660 (p = 0.146) |
| FPR sobre No Tóxico (migrantes + externo 2) | 0.122 | **0.109** |
| Vulgaridad afectiva | 19/20 · 18/18 | 19/20 · 18/18 |
| Atajos (6 familias) | 1.00 | 1.00 |
| ECE test tras T | 0.032 | 0.019 |

**Límites:** la mejora de Amenazas (recall 0.477) sigue lejos de lo deseable y su ganancia sobre v3.2.0 en ese hilo no es significativa por McNemar (p = 0.146) aunque sí lo es en F1 de la clase para v3.3.0-rc1 solo (IC [+0.011, +0.120]); el test oficial baja 0.004 (no significativo); las 4 pérdidas de batería de v3.3.0-rc1 solo (dos ataques con emoji, una grosería afectiva) no se reproducen en el ensamble. Las etiquetas de los hilos son consenso de agentes, sin validación humana. Rollback: cambiar `MODELOS` en `app/api/main.py` a `models/v3.2.0`.

## Banco externo real (n = 1,160): comparación de todas las versiones (15 de octubre de 2026)
`src/evaluation/banco_externo.py`: migrantes (307) + externo 2 (650) + militares_pandilleros (203), consenso de 3 anotadores, ninguna versión lo vio al entrenar. Clases NT/OF/OD/AM: 788 / 225 / 36 / 111.

| Versión | Acierto | F1-macro [IC 95 %] | Recall NT / OF / OD / AM | FPR sobre NT |
|---|---|---|---|---|
| v3.0.0 | 0.729 | 0.588 [0.546, 0.628] | 0.731 / 0.880 / 0.528 / 0.477 | 0.269 |
| v3.1.0 | 0.793 | 0.638 [0.591, 0.681] | 0.846 / 0.844 / 0.556 / 0.387 | 0.154 |
| **v3.2.0** | **0.822** | **0.679** [0.630, 0.721] | 0.877 / 0.867 / 0.583 / 0.423 | 0.123 |
| v3.3.0 (en la API) | 0.823 | 0.668 [0.619, 0.711] | 0.890 / 0.818 / 0.500 / 0.468 | **0.110** |

Pareado: v3.0.0 → v3.1.0 ΔF1 +0.050 (IC [+0.018, +0.082], p < 0.0001); v3.1.0 → v3.2.0 ΔF1 +0.041 (IC [+0.015, +0.067], p < 0.0001); **v3.2.0 → v3.3.0 ΔF1 −0.011 (IC [−0.037, +0.012], McNemar b/c 22/21, p = 1.0)**.

**Lectura honesta:** las mejoras v3.0.0 → v3.1.0 → v3.2.0 se confirman con 1,160 textos reales. **v3.3.0 no es mejor que v3.2.0 en el banco completo**: empata en acierto (0.823 vs 0.822), mejora Amenazas (recall 0.423 → 0.468) y falsos positivos (0.123 → 0.110), pero baja Ofensivo (0.867 → 0.818) y Odio (0.583 → 0.500; son 36 casos, 3 menos). Es un intercambio, no una mejora. La promoción de v3.3.0 se hizo con la evidencia disponible en ese momento (hilo reservado de Amenazas), y la persona responsable puede revertirla cambiando `MODELOS` en `app/api/main.py` a `models/v3.2.0`.

## Banco externo ampliado con Odio (n = 2,042) — 16 de octubre de 2026
Se añadieron 882 textos de 4 hilos de LGBT, racismo y xenofobia (consenso de 3 anotadores; κ entre los dos primeros = 0.885; 195 de Odio). Banco: NT/OF/OD/AM = 1,203 / 451 / 231 / 157.

| Versión | Acierto | F1-macro [IC 95 %] | Recall NT / OF / OD / AM | FPR sobre NT |
|---|---|---|---|---|
| v3.0.0 | 0.648 | 0.575 [0.548, 0.600] | 0.635 / 0.800 / 0.532 / 0.484 | 0.365 |
| v3.1.0 | 0.716 | 0.609 [0.582, 0.636] | 0.780 / 0.765 / 0.506 / 0.401 | 0.220 |
| **v3.2.0** | 0.745 | **0.637** [0.610, 0.664] | 0.814 / 0.776 / 0.550 / 0.414 | 0.186 |
| v3.3.0 (en la API) | 0.742 | 0.631 [0.604, 0.658] | 0.824 / 0.752 / 0.498 / 0.446 | 0.176 |

Pareado: v3.0.0 → v3.1.0 ΔF1 +0.034 (p < 0.0001); v3.1.0 → v3.2.0 +0.028 (p < 0.0001); **v3.2.0 → v3.3.0 −0.006 (IC [−0.020, +0.008], McNemar p = 0.62): sin diferencia**.

**Hallazgo principal: el Odio es ahora la debilidad mayor.** Ninguna versión detecta más de 55 % del discurso de odio en hilos de LGBT, racismo y xenofobia (recall 0.50–0.55; v3.3.0 es la peor, 0.498). En el banco de esos 4 hilos el acierto va de 0.54 a 0.64. v3.3.0 mantiene la mejora en Amenazas (0.446 vs 0.414) a costa de Odio y Ofensivo.
Siguiente paso en curso: v3.4.0-rc1 (v3.3.0-rc1 + 3 hilos de Odio; se reserva `xenofobia_federico`), con criterios fijados antes en `src/evaluation/comparar_v340.py`.

## Plan de mejora aprobado — Fase 0 completada (16 de octubre de 2026)
Plan en `docs/improvement/Plan_mejora.md` (aprobado por la persona responsable): validadores = agentes, despliegue local, un solo modelo mediante destilación, metas medibles, banco congelado y regla de parada. Fase 0: constructor único `build_dataset_final.py` con autotest de fugas (ambas comprobaciones OK), banco congelado con hashes, pool de 14 hilos con etiquetas blandas, constructores viejos archivados. `v3.4.0-rc1` (exploratorio) se evalúa contra el banco congelado y **no se adopta**.

### Línea base oficial sobre el banco congelado (n = 1,391; NT/OF/OD/AM = 855 / 289 / 130 / 117)
| Versión | Acierto | F1-macro [IC 95 %] | Recall NT / OF / OD / AM | FPR sobre NT |
|---|---|---|---|---|
| v3.0.0 | 0.709 | 0.633 [0.600, 0.664] | 0.698 / 0.858 / 0.638 / 0.496 | 0.302 |
| v3.1.0 | 0.775 | 0.672 [0.637, 0.705] | 0.829 / 0.837 / 0.608 / 0.410 | 0.171 |
| v3.2.0 | 0.799 | **0.699** [0.665, 0.732] | 0.858 / 0.841 / 0.631 / 0.444 | 0.142 |
| **v3.3.0 (API)** | 0.796 | 0.693 [0.659, 0.726] | 0.871 / 0.796 / 0.577 / 0.487 | **0.129** |

Pareado: v3.0.0 → v3.1.0 +0.039 (p < 0.0001); v3.1.0 → v3.2.0 +0.027 (p = 0.0001); v3.2.0 → v3.3.0 −0.007 (p = 0.69). Esta es la línea base contra la que se mide todo el plan. El experimento exploratorio v3.4.0-rc1 se interrumpió (suspensión del equipo) y se descartó: el plan lo dejaba como no adoptable.


## v3.4.0 — modelo único, fases 2–5 del plan (15 de octubre de 2026)
Una sola medición sobre el banco congelado (n = 1,391; `reports/improvement/fase3_candidatos.md`, `src/evaluation/comparar_fase3.py`). Selección: CV por hilo (Optuna), no el banco.
- **Fase 2 (Optuna, 12 pruebas, CV por hilo de 2 pliegues):** receta actual 0.6312 → mejor 0.6486 (lr 3.92e-5, 4 épocas, wd 0.0060, warmup 0.116, peso de hilos 1.53, peso de clase Odio/Amenazas ×1.91).
- **Fase 3 (3 semillas por candidato):**

| Modelo | F1-macro banco [IC] | Odio | Amenazas | Ofensivo | FPR | Test oficial |
|---|---|---|---|---|---|---|
| v3.3.0 (10 modelos) | 0.693 [0.659, 0.726] | 0.577 | 0.487 | 0.796 | 0.129 | 0.839 |
| A (receta actual + todo el pool) | 0.713 [0.680, 0.747] | 0.608 | 0.453 | 0.824 | 0.106 | 0.847 |
| B (receta Optuna) | 0.714 [0.682, 0.747] | 0.631 | 0.470 | 0.810 | 0.111 | 0.831 |
| C = A + B (6 modelos) | 0.716 [0.683, 0.749] | 0.608 | 0.470 | 0.827 | 0.109 | 0.840 |

  Todos mejoran a v3.3.0 en FPR (≤ 0.12 ✔) y F1 (≥ 0.70 ✔), con ΔF1 ≈ +0.02 (IC pareado cruza cero; McNemar p 0.018–0.048). **Ninguno alcanza Amenazas ≥ 0.60 ni de forma robusta Odio ≥ 0.65.** C se elige como profesor (mejor F1, sin empeorar Ofensivo ni FPR).
- **Fase 4 (destilación a un solo modelo, 1 semilla):** configuración preregistrada (T 2, α 0.7) falló (Odio 0.485, test 0.808). Se probó una malla declarada de 3 variantes más; se eligió por **F1 de validación oficial** (no por el banco): T 1, α 0.5, receta B. Con 3 semillas: F1 banco 0.720 / 0.707 / 0.723 (media 0.717 ≈ 100 % del ensamble C), Odio 0.669 / 0.585 / 0.623 (media 0.626), Amenazas 0.470 / 0.496 / 0.504, FPR ≈ 0.111, test oficial 0.832 / 0.821 / 0.823. **Se despliega la semilla 42** (la de mejor F1 de validación entre las semillas no era la 42; se mantuvo la semilla fija por regla; sus 6/7 metas se deben en parte a la suerte de la semilla: la media entre semillas es la cifra honesta).
- **Fase 5 (sesgos, `reports/improvement/fairness.md`):** brecha de F1 X − Facebook 0.103; FPR sobre No Tóxico **con jerga 0.379 vs sin jerga 0.074** en el test oficial (n = 29 con jerga; en v3.3.0 era 0.241): **v3.4.0 marca más texto no tóxico con jerga**; sonda afectiva 18/20 · 17/18 (v3.3.0: 19/20 · 18/18, ambas por encima del umbral). Odio por grupo: etnia 0.90, nacionalidad 0.81, LGBT 0.92 (n = 13), «otro» 0.61; mujeres/género sin potencia (n = 4). Sobremarcado de menciones de nacionalidad: 21.8 % de los No Tóxico que las mencionan.
- **Tamaño:** 418 MB (un modelo) frente a ≈ 5 GB (v3.3.0, 10 modelos).
- **Lecciones:** dos entrenamientos simultáneos en una GPU de 8 GB la saturan (10× más lento); inferencia por lotes en `probs_propio` (diferencia 9e-7, mismas predicciones).
