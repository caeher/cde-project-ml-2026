# Review del proyecto — Análisis del discurso de odio en redes sociales de El Salvador

**Estado al 7 de octubre de 2026**
**Equipo:** Willian Chávez (datos, normalización, auditoría, estadística) · Cristian Escalante (mBERT) · Julio De La Quadra (XLM-R)
**Repositorio del equipo:** github.com/caeher/cde-project-ml-2026, rama v3

---

## 1. En una línea

El proyecto alcanzó la meta (F1-macro 0.8529, IC 95 % [0.8191, 0.8858]) con RoBERTuito en ensemble de tres semillas. El límite actual no es el modelo: son los **2,144 textos reales**, el **acuerdo entre anotadores de 0.8095** y la debilidad en **Facebook, ironía y sarcasmo**. Los 4,074 textos de X recolectados en octubre ayudan en X y perjudican en Facebook. Todavía no se reentrenó RoBERTuito con ellos.

---

## 2. Objetivo y diseño fijo

| | |
|---|---|
| Tarea | Clasificación de una etiqueta, 4 clases, precedencia por severidad |
| Clases | 0 No Tóxico · 1 Lenguaje Ofensivo · 2 Discurso de Odio · 3 Amenazas/Violencia |
| Meta | F1-macro ≥ 0.80 sobre test, **con el extremo inferior del IC** |
| Splits fijos | val 459 · test 460 — sin cambios desde julio (SHA-256 test `5d1284efcc7df20f…`) |
| Regla de etiquetado clave | La afiliación política **no** es grupo protegido → Lenguaje Ofensivo (`docs/guia_anotacion.md` §3.1) |
| Normalización | Una sola fuente: `src/features/normalization.py`. Conserva tildes, mayúsculas y ortografía original; anonimiza @ y URL; demojiza en español |

---

## 3. Cronología

### Julio — datos
- Ordenamiento del proyecto, EDA y normalización con criterio de preservación máxima (no corregir faltas: así llega el input real).
- Mapeo de 16 etiquetas originales a 4 (`src/data/label_mapping.py`); fuga de PII por `URL_Original` eliminada.
- Hallazgo: **215 textos de fútbol etiquetados como odio** solo por mencionar países (sobreetiquetado temático).
- Split v1: train 2,144 · val 459 · test 460.

### Agosto — auditoría de la Etapa I
- Errores en los informes de ambos compañeros: FPR escrito a mano, cifras copiadas entre modelos, slices nunca ejecutados.
- Inferencia de XLM-R en NumPy puro, porque el entorno no admite torch.
- **Atajo del emoji:** el 89 % de los textos con emoji eran Lenguaje Ofensivo.
- **Dataset B2:** 1,149 sintéticos dirigidos (emojis, amenazas ofuscadas, jerga inofensiva). Batería adversarial de 75 → **144 casos** (grupos A–G).

### 1 de septiembre — verificación independiente (reejecución de pesos)
| | mBERT v1 | XLM-R v1 |
|---|---|---|
| F1-macro test | 0.7777 | 0.8058 |
| Batería 144 | 74 | 74 |
| FPR No Tóxico con jerga / sin jerga | 0.414 / 0.160 | 0.448 / 0.160 |

McNemar entre ambos: p = 0.20, empate. Un emoji inocuo volvía tóxico un texto neutro en 75–88 % de los casos. Se perdían 7 de cada 10 amenazas ofuscadas.

### 12 de septiembre — entrega 2v
- Cristian adoptó B2: F1 0.7610, batería 120/144, amenazas ofuscadas 11/11. Informe con la conclusión del McNemar **invertida** (favorecía a XLM-R, no a mBERT).
- Julio: filtro regex post-hoc que se evade anteponiendo «gracias»; reportó sobre un conjunto de N = 1050 que no existe en el proyecto; sin F1-macro.
- Informe: `reports/Revision_Entrega_2v.md`.

### Etapa II — sistema final (repo v3)
| | |
|---|---|
| Modelo | RoBERTuito (109 M), ensemble de 3 semillas (42, 1337, 2026), voto blando |
| Corpus | 6,416 train = 2,144 reales + 1,140 sintéticos previos + 3,132 dirigidos |
| Hiperparámetros (Optuna, 20 pruebas) | lr 5.73e-5 · batch 32 · 6 épocas · wd 0.0176 · warmup 0.0929 · peso sintéticos 0.75 · pesos por clase |
| **F1-macro test** | **0.8529**, IC [0.8191, 0.8858], 394/460 |
| Modelo individual | 0.8268, IC [0.7912, 0.8610] — **cruza la meta** |
| Validación cruzada | 0.8274 ± 0.0170 (5 pliegues, solo texto real) |
| Batería 144 / sonda 204 | 127 / 202 (tras el arreglo del atajo) |
| FPR jerga | 41–45 % → **27.6 %** (n = 29, sin potencia) |
| Puntos débiles | Sarcasmo 0.4947 · Ironía 0.5250 · Facebook 0.7640 · ECE 0.1214 |

Hallazgos clave de la etapa:
- **El dominio de preentrenamiento importó más que el tamaño:** XLM-R large (560 M) rindió peor que RoBERTuito (109 M) y tardó 28 veces más. Los modelos de la Etapa I fueron los dos peores de siete.
- **Atajo sintáctico:** «voy a comer» → Amenaza (82.6 %). El generador solo rellenaba «te voy a…» con verbos violentos. Se corrigió con 219 contraejemplos.
- **Sin reglas post-hoc:** con el prefijo «gracias», el prototipo anterior dejaba pasar 20 de 100 amenazas; el modelo nuevo, 5.

**Errores en el reporte de la Etapa II, pendientes de corregir:**
1. §12.2 afirma que el IC del modelo individual (0.7912) supera 0.80. No lo supera; la Tabla 13 marca «Sí» por error.
2. §12.4 dice que las tres comparaciones de McNemar son significativas. Con p = 0.282 / 0.0026 / 0.0567, solo una lo es.
3. §12.3: la prosa (0.8308, 0.8488) contradice la Tabla 14 (0.8020, 0.8293).
4. Menores: Tabla 8 «0 épocas solo reales» contra «tres» en el texto; la Tabla 16 contra la 20 (125 vs 127); semilla 2026 0.8555 vs 0.8562; la Tabla 11 dice «seis» y tiene cuatro filas; los cortes de la Tabla 21 no suman 460.

Preparado para la defensa: `docs/Guion_Presentacion_EtapaII.md` (30 min, palabra por palabra) y `docs/Cuestionario_Defensa_EtapaII.md` (30 preguntas).

### 7 de octubre — datos nuevos de X
- Recibidos: 4,328 filas reales de X en `data/new-10-7-2026/`. Cada archivo trae una sola clase: Willian, Amenazas + No Tóxico; Cristian, Ofensivo; Julio, Odio.
- Limpieza (`src/data/build_dataset_v4.py` → `data/dataset_v4/`):
  - −80 que ya estaban en val/test
  - −6 por conflicto de etiqueta entre anotadores
  - −3 duplicados internos y −168 que ya estaban en el train
  - **384 reetiquetadas de Odio a Ofensivo** (insultos políticos que contradecían la guía)
  - 23 filas de fuga heredada quitadas del train B2
  - Resultado: **4,074 incorporadas**; train v4 de 7,344 filas sobre la base B2
- Proxy lineal (TF-IDF + LinearSVC):
  - Sin la corrección de etiquetas, los datos nuevos empeoraban el modelo de forma significativa (p = 0.024). Con ella, quedan neutrales.
  - Por plataforma: **X +2.2 puntos, Facebook −4.8**. Bajarles el peso no resuelve el intercambio.
- `src/train/entrenar_v4.py`: reentrenamiento de RoBERTuito con la configuración de la Etapa II. **No se pudo ejecutar** porque el entorno de Claude no tiene GPU ni torch.

### 7 de octubre (tarde) — dataset v4 rehecho sobre la Etapa II
- **Defectos encontrados y corregidos:**
  - `entrenar_v4.py` no replicaba la Etapa II: usaba `robertuito-base-uncased` en minúsculas (la Etapa II usó `-cased`) y dejaba con peso 1.0 los 3,132 sintéticos `v3_*`. Se reescribió siguiendo `src/v3/entrenar.py`: pérdida Σ(w·ℓ)/Σw, early stopping 2, batería normalizada desde el texto crudo.
  - El `normalization.py` local era la v1.1; la Etapa II usó la **v1.2** (no rompe `m@ldito`, 🔫 = pistola). Ahora hay una sola: la v1.2.
  - **21 filas del train de la Etapa II solapaban:** 1 con val y 20 sintéticos con la batería (misma frase, otro emoji). El test estaba limpio: el 0.8529 se sostiene; el 127/144 pudo estar favorecido.
- **Dataset v4 v2** (`data/dataset_v4/`, base `data/dataset_v3/train.csv`): **10,469 filas** = 2,143 reales + 4,252 sintéticas + 4,074 de octubre. Línea base sin octubre: 6,395. Huella `36617f83838f77c3`, igual en la PC y en la nube. La versión anterior quedó en `archivo/2026-10-07_v4_normalizacion_v1.1/`.
- **Proxy lineal sobre el v2** (`logs/2026-10-07_proxy_lineal_v1.1_vs_v1.2.log`): X +2.2 a +2.8 puntos, Facebook −2.3 a −4.5, total ±0.01; **ninguna diferencia significativa** (p ≥ 0.21). No reproduce las cifras del README v1 (configuración original desconocida).
- `notebooks/03_reentrenar_v4_colab.ipynb`: notebook autocontenido para Colab (corrida v4 + línea base + comparación pareada). **El reentrenamiento de RoBERTuito sigue sin ejecutarse.**

---

## 4. Lecciones que atraviesan el proyecto

1. **Reproducir, no creer.** Casi cada entrega tuvo una cifra que no coincidía con sus propios pesos o tablas.
2. **Con n = 460, diferencias de 2–3 puntos son ruido.** La dispersión entre semillas es de 1.8 puntos. Para separar Δ = 0.028 harían falta unos 1,800 ejemplos de test.
3. **Cada atajo vino de un generador o una recolección sin contraejemplos:** emoji ⇒ ofensivo, «te voy a» ⇒ amenaza, y ahora el riesgo de que la consulta de búsqueda ⇒ clase.
4. **Las etiquetas son el techo:** 0.8095 de acuerdo. Los errores de etiquetado (fútbol como odio, política como odio) se propagan directo al modelo.
5. **Las métricas agregadas no ven los modos de fallo que el test no muestrea:** el atajo sintáctico tocaba solo el 3 % del test.

---

## 5. Pendientes, en orden

| # | Tarea | Quién | Nota |
|---|---|---|---|
| 1 | Ejecutar `notebooks/03_reentrenar_v4_colab.ipynb` en Colab (GPU): corrida v4 y línea base, mismas semillas | Cristian / Willian | Todo listo; devuelve `resultados_v4.zip` |
| 2 | Comparar con McNemar (`src/evaluation/comparar_modelos.py`) y por plataforma | Willian | Decidir si se adopta el v4 |
| 3 | Validar las 4,074 etiquetas nuevas con un segundo anotador, al menos una muestra estratificada | Equipo | Hoy todas tienen `Validado = NO` |
| 4 | Corregir los 3 errores graves del reporte de la Etapa II | Willian | Son de redacción, no de resultados |
| 5 | Recolectar datos de **Facebook**, ironía y sarcasmo | Equipo | Es el punto débil real |
| 6 | Ampliar el test hacia unos 1,800 ejemplos | Equipo | Sin tocar el test actual: agregar un test 2 |
| 7 | Calibración por temperature scaling | — | ECE 0.1214 |
| 8 | Decidir qué hacer con las 230 filas `fuera_de_sv` | Equipo | Ablación con `--excluir_fuera_sv` |

---

## 6. Mapa de archivos

| Ruta | Qué es |
|---|---|
| `docs/guia_anotacion.md` | Guía de etiquetado v2.0, la fuente de verdad de las clases |
| `src/features/normalization.py` | Normalizador único (train, eval, API) |
| `src/data/label_mapping.py` | Mapeo 16 → 4 |
| `src/data/build_dataset_b2.py` · `augmentation.py` · `lexicon_emojis.py` | B2 y sintéticos |
| `src/data/build_dataset_v4.py` | Dataset v4 con los datos de octubre |
| `src/train/entrenar_v4.py` | Reentrenamiento de RoBERTuito (requiere GPU) |
| `src/audit/mbert_numpy.py` · `xlmr_numpy.py` | Inferencia sin torch, validada contra métricas oficiales |
| `src/evaluation/comparar_modelos.py` | McNemar pareado y bootstrap del Δ |
| `data/dataset_b2/` | B2 + `test_adversarial.csv` (144 casos) |
| `data/dataset_v4/` | Train de 7,344 + val/test intactos + README |
| `data/new-10-7-2026/` | Los 3 CSV crudos de octubre |
| `reports/Informe_Verificacion_de_Modelos.docx` | Verificación del 1 de septiembre |
| `reports/Revision_Entrega_2v.md` | Revisión del 12 de septiembre |
| `reports/v4_filas_con_fuga.csv` · `v4_conflictos_etiqueta.csv` | Trazabilidad de la limpieza v4 |
| `docs/Guion_Presentacion_EtapaII.md` · `Cuestionario_Defensa_EtapaII.md` | Defensa |

---

## 7. Restricciones del entorno de Claude

- La terminal corre en un Linux aislado (2 CPU, 3 GB de RAM, sin GPU). No ve el Python de Windows.
- `download.pytorch.org` está bloqueado. torch de PyPI pesa 555 MB más unos 2 GB de dependencias CUDA y no cabe con holgura.
- Cada comando tiene un límite de 10 minutos y los procesos en segundo plano mueren entre comandos.
- **Se puede:** preparar datos, sklearn, inferencia en NumPy, estadística e informes.
- **No se puede:** entrenar transformers. Eso va a Colab o a la GPU de un compañero.

---

## 8. Actualización del 7 de octubre (tarde) — reentrenamiento v4 ejecutado

Se entrenó en la RTX 4060 local (no hizo falta Colab). Detalle y cifras: `reports/Resultado_reentrenamiento_v4.md`. Todo recalculado con `src/evaluation/comparar_v4.py` desde las probabilidades.

| Corrida | F1 val | F1 test | IC 95 % test | Extremo inf. ≥ 0.80 |
|---|---|---|---|---|
| Base, 3 semillas, sin octubre | 0.8537 | 0.8358 | [0.7994, 0.8693] | no |
| v4, octubre con peso 1.0 | 0.8365 | 0.8340 | [0.7980, 0.8673] | no |
| v4, octubre con peso 0.3 | 0.8517 | 0.8390 | [0.8041, 0.8727] | sí (no seleccionada) |
| v4, peso 0.3, sin fuera de SV | 0.8437 | 0.8308 | [0.7944, 0.8643] | no |
| **Base, 5 semillas, sin octubre** | **0.8621** | **0.8499** | **[0.8143, 0.8820]** | **sí** |

- Los datos de octubre no mejoran el modelo (todos los McNemar p ≥ 0.85, Δ ≈ 0). No se adoptan.
- La base de 5 semillas gana en val y cumple la meta con el IC. Su ventaja sobre la de 3 semillas no es significativa (p = 0.21).
- La línea base reproduce 0.8358, no el 0.8529 de la Etapa II (diferencia ≈ la dispersión entre semillas, de ≈ 0.018).
- Calibración: temperature scaling (T = 1.349) baja el ECE en test de 0.0561 a 0.0271 sin cambiar predicciones.
- Quedan sin cambios y dependen del equipo: datos de Facebook/sarcasmo/ironía, segundo anotador sobre octubre, test ampliado, y pegar `docs/Fe_de_erratas_EtapaII.md` en el reporte del repo del equipo.

**Alcance acordado el 7 de octubre:** se descartan la recolección de Facebook y las categorías de sarcasmo/ironía (las clases son solo 4; esos campos son cortes de análisis). Facebook, sarcasmo e ironía pasan a **limitaciones conocidas** de la tesina. El pendiente 5 de la §5 queda cerrado por decisión del equipo. El modelo final no usa los datos de octubre, así que el segundo anotador ya no bloquea nada.
