# Plan: llevar el modelo de toxicidad/odio a un nivel entregable (Etapa II + defensa)

## Context
Proyecto de especialización (UES): clasificador de 4 clases (No Tóxico, Ofensivo, Odio, Amenazas) para X/Facebook de El Salvador. Se evalúa con la rúbrica de la **Etapa II** (100 pts: hiperparámetros 20, modelos avanzados + ensemble 20, evaluación rigurosa 15, **fairness 15**, **prototipo desplegado 15**, **impacto social 15**; documento ≤ 40 págs.) y luego la **defensa** (tesina 50–70 págs., video ≤ 3 min, presentación 15 min, GitHub público).

Estado medido sobre el **banco congelado** (n = 1,391, consenso de 3 anotadores): v3.3.0 → F1-macro 0.693, recall Odio 0.577, Amenazas 0.487, falsos positivos 0.129 (v3.2.0: 0.699 / 0.631 / 0.444 / 0.142). La persona responsable considera el modelo «verde e impreciso» y quiere mejorarlo **rápido con IA**, sin personas validando (validan agentes), prototipo **local**, y pregunta por qué hay 10 modelos.

El problema de estrategia: hasta ahora se iteró ad hoc (recolectar 3 hilos → entrenar → evaluar → repetir), con test móvil, >10 comparaciones sobre los mismos datos y sin meta ni parada. Este plan fija presupuesto, banco congelado y criterio de parada.

## Decisiones ya tomadas por la persona responsable
- Validadores = **agentes** (3 independientes a ciegas + desempate). Sin humanos.
- Despliegue = **local** + video demo.
- Prioridad = **mejorar el modelo**; los 10 modelos deben reducirse a **uno solo** (destilación).

## Metas medibles (una sola medición final, sobre el banco congelado)
| Métrica | Hoy (v3.3.0) | Meta |
|---|---|---|
| Recall de Odio | 0.58 | ≥ 0.65 |
| Recall de Amenazas | 0.49 | ≥ 0.60 |
| Falsos positivos sobre No Tóxico | 0.13 | ≤ 0.12 |
| F1-macro (banco) | 0.69 | ≥ 0.70 (**casi alcanzada; se propone subir a ≥ 0.75**) |
| Test oficial F1-macro | 0.839 | ≥ 0.83 |
| Groserías afectivas salvadoreñas | 19/20 · 18/18 | ≥ 17/20 · ≥ 16/18 |
| Modelo desplegado | 10 modelos (≈ 5 GB) | **1 modelo (≈ 0.5 GB)** con ≥ 97 % del F1 del ensamble |

## Reglas que no cambian
- **Banco congelado** (nunca entrena, nunca decide): `migrantes`, `externo 2`, `militares_pandilleros`, `xenofobia_federico`, test oficial. Hilos nuevos que se agreguen al banco forman un «banco v2» aparte.
- **Selección por validación cruzada por hilo** sobre el pool de entrenamiento, no mirando el banco.
- **Candidatos fijados ahora** (fase 3); nada de variantes nuevas a mitad de camino.
- Batería de 144 = solo diagnóstico.
- **Limitación declarada** en la tesina: validadores y anotadores son LLM → errores correlacionados. Mitigación: etiquetado a ciegas, guía fija, modelos distintos entre anotadores (p. ej. Sonnet / Opus / Haiku), reporte de κ, banco por consenso.

## Fases

### Fase 0 — Congelar y ordenar (1 sesión)
- Un solo constructor `src/data/build_dataset_final.py` que parta de las tablas de consenso (`data/hilos_reales/etiquetas/consenso_*.csv`) y de `data/dataset_v4`/`v8`, excluya el banco y falle ante cualquier fuga. Sustituye a `build_dataset_v5/v6/v7/v8.py` (se dejan en `archivo/`).
- Lista del banco y del pool en `data/hilos_reales/REGISTRO.md`; hashes SHA-256 de los conjuntos del banco.
- Reutilizar: `src/evaluation/banco_externo.py`, `comparar_candidato.py`, `prueba_atajos*.py`, `probe_vulgaridad_afectiva_SOLO_EVALUAR.csv`.

### Fase 1 — Datos a escala con IA (2 rondas máx.)
Cuello de botella actual: Odio ≈ 330 y Amenazas ≈ 200 en entrenamiento. **Cuota**: ≥ 700 Odio y ≥ 450 Amenazas con consenso.
- Recolección con BrowserOS (patrón ya probado en `run`: 4 hilos en paralelo, ≈ 1 min por hilo, ≈ 250 textos): 16–24 hilos dirigidos a Odio (nacionalidad/migración, LGBT, misoginia, racismo, con casos salvadoreños) y Amenazas (pandillas/CECOT, ataques políticos).
- Etiquetado: 2 agentes ciegos + desempate (patrón de `lote_*.csv` → `salida_*.csv` → consenso). **Etiquetas blandas**: guardar la fracción de anotadores que votó cada clase para usar en destilación.
- Se **detiene** al alcanzar la cuota o tras 2 rondas.

### Fase 2 — Optimización de hiperparámetros (rúbrica 20 pts)
- Optuna sobre el pool (leave-one-thread-out, 1 semilla, ≈ 20 pruebas × 3 min en la GPU local): lr, épocas, warmup, weight decay, peso de clase de Odio/Amenazas, peso de filas de hilos. Demuestra «mejora significativa vs baseline» (baseline lineal TF-IDF + SVC ya medido).
- Reutilizar: `src/train/entrenar_v5.py` (acepta `--peso_hilos`, `--extra`, `--seeds`).

### Fase 3 — Modelos avanzados y ensemble (rúbrica 20 pts), tres candidatos fijos
- **A.** Receta actual con todo el pool.
- **B.** A con hiperparámetros de la fase 2 y peso de clase aumentado para Odio y Amenazas.
- **C.** Ensamble A + B (5 + 5 semillas).
Se elige por CV por hilo. Se descarta cualquiera que empeore Ofensivo o falsos positivos > 0.03.

### Fase 4 — Un solo modelo: destilación
- Estudiante: un RoBERTuito entrenado con las probabilidades del ensamble ganador (soft labels) más las etiquetas blandas de los anotadores; opcionalmente con hilos recolectados sin etiquetar (pseudo-etiquetas del ensamble, solo como regularización).
- Criterio: estudiante ≥ 97 % del F1-macro del ensamble en el banco, sin perder Odio ni Amenazas más de 0.03, groserías afectivas ≥ 17/20.
- Despliegue: `app/api/main.py` ya soporta carpeta con `manifest.json`; el estudiante usa la rama de una sola carpeta (`semilla_*/modelo`).

### Fase 5 — Informe de sesgos y ética (rúbrica 15 pts)
Script nuevo `src/evaluation/fairness.py` sobre el banco + test oficial:
- por plataforma (X vs Facebook), por grupo objetivo (mujeres, LGBT, nacionalidades, etnia), por jerga salvadoreña vs no jerga;
- recall/FPR por grupo con IC bootstrap y disparidad máxima;
- intercambio contrafactual de grupo (`prueba_atajos_reales.py` ya existe) y groserías afectivas;
- mitigaciones aplicadas y límites (anotadores LLM, datos de X, sin Facebook).

### Fase 6 — Prototipo local + video (rúbrica 15 pts)
- Streamlit (`app/ui/app.py`) + API local con el estudiante: añadir panel de probabilidades, advertencia de baja confianza y ejemplos precargados.
- Guion del video de 3 min y script de arranque (`scripts/arrancar_demo.ps1`).

### Fase 7 — Documentos (≈ 15 págs. por sesión)
- Etapa II (≤ 40 págs.) mapeado 1:1 a la rúbrica; aplicar `docs/Fe_de_erratas_EtapaII.md`.
- Sección de **impacto social y recomendaciones de política pública** (moderación asistida con humano en el bucle, umbrales por clase, riesgos de falsos positivos con jerga, transparencia, retención de datos).
- Tesina, presentación de 15 min y repo público limpio (sin datos personales; solo IDs y consenso).

## Regla de parada
Se detiene cuando ocurra lo primero: (1) metas alcanzadas; (2) se completa la fase 4 aunque no se alcancen, y se documenta como límite; (3) se agotan las 2 rondas de la fase 1 sin acercarse a las cuotas.

## Archivos críticos
- Nuevos: `src/data/build_dataset_final.py`, `src/evaluation/fairness.py`, `src/train/destilar.py`, `src/train/optuna_cv_hilo.py`, `scripts/arrancar_demo.ps1`.
- Se modifican: `app/api/main.py` (modelo único), `app/ui/app.py` (panel), `CHANGELOG.md`, `docs/Plan_mejora.md` (reemplazar por este plan).
- Se reutilizan sin cambios: `src/train/entrenar_v5.py`, `src/evaluation/{banco_externo,comparar_candidato,combinar_modelos,prueba_atajos,prueba_atajos_reales}.py`, `src/features/normalization.py`.

## Verificación
- Fase 0: el constructor falla si se inserta un texto del banco en el pool (prueba de fuga).
- Fase 1–3: `python src/evaluation/banco_externo.py` imprime tabla comparable entre versiones; metas contra la tabla de arriba.
- Fase 4: estudiante vs ensamble en el banco con McNemar pareado; `curl -X POST localhost:8000/predecir` y `streamlit run app/ui/app.py` funcionan con un único modelo; tamaño en disco ≈ 0.5 GB.
- Fase 5: `fairness.py` genera `reports/fairness.md` con tablas por grupo e IC.
- Fase 7: documento y diapositivas con todas las cifras recalculadas desde predicciones, no copiadas.

## Riesgos honestos
- Las etiquetas del pool y del banco las generan agentes; las mejoras pueden reflejar el sesgo del anotador LLM, no la realidad. Se declara como limitación.
- Si BrowserOS se desconecta, la fase 1 se retrasa (ya pasó varias veces; hay que re-listar pestañas tras reconectar).
- El banco tiene pocos casos de Odio por hilo; las metas de Odio tendrán IC amplios.

## Registro de desviaciones y avance (15 de octubre de 2026)
- **Semillas de los candidatos:** A y B se entrenan con **3 semillas** (42, 1337, 2026), no 5, para ahorrar ≈ 30 min de GPU; C = A + B queda con 6 modelos. La Etapa II también usó 3 semillas. Decisión de la persona responsable: acelerar.
- **Fase 2 terminada** (`reports/optuna_cv_hilo.json`, 12 pruebas, CV por hilo de 2 pliegues): receta actual 0.6312 → mejor 0.6486 (lr 3.9e-5, 4 épocas, wd 0.0060, warmup 0.116, peso de hilos 1.53, peso de clase extra ×1.91). Mejora de ≈ 1.7 puntos de F1-macro; es pequeña y con una sola semilla por prueba.
- **Lección de operación:** dos entrenamientos simultáneos en la GPU de 8 GB la saturan (la velocidad cae ≈ 10 veces). Una tarea de GPU a la vez (`scripts/pipeline_fase3.sh`).
- **Inferencia por lotes** en `combinar_modelos.probs_propio` (diferencia máxima con la versión por texto: 9e-7; mismas predicciones).
