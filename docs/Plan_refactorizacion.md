# Plan de reestructuración del proyecto (v2, para aprobar)

**Alcance:** solo **reordenar**. No se borra nada, no se reescribe lógica y no cambia ninguna cifra. `src/` se mantiene como está (plano, con sus subcarpetas). Lo único que cambia en el código son las **rutas** a archivos que se mueven.

## 1. Diagnóstico (medido en el repo, 16-oct-2026)

### 1.1 `data/` — 21 carpetas sin orden de propósito
Mezcla cuatro cosas distintas al mismo nivel:

| Qué es | Carpetas hoy |
|---|---|
| **Fuentes** (lo recolectado) | `raw/` (corpus salvadoreño, léxicos), `new-10-7-2026/` (X, oct. 2026), `external/` (vacía) |
| **Anotación** | `interim/` (anotación LLM, adjudicación, gold de la Etapa I), `hilos_reales/` (118 archivos: `crudo/`, `crudo_fase1/`, `ciego/` con 31 lotes + 47 salidas, `etiquetas/` con consensos **y 5 scripts `lab*.py`**, `predicciones/`, `revision/`) |
| **Datasets por versión** | `processed/` (v1, Etapa I), `dataset_b2`, `dataset_v3` (Etapa II), `dataset_v4`, `v5a`, `v5f`, `v6`, `v7`, `dataset_final`; y fuera de `data/`: `archivo/datasets/dataset_v8` y `dataset_v7_copia` |
| **Conjuntos de evaluación** | `banco_congelado/`, `hard_cases/` |

Además:
- **Copias idénticas byte a byte:** `val.csv`, `test.csv` y `test_adversarial.csv` están repetidos en 7–8 carpetas (`dataset_final` = `v5a` = `v5f` = `v6` = `v7` = `v8` = `v7_copia`; `b2` = `v3`). `archivo/datasets/dataset_v7_copia` es una copia completa de `data/dataset_v7`. `test_externo_migrantes.csv` está 5 veces.
- **No hay un mapa** de qué versión se construyó a partir de cuál, ni qué script la generó.

### 1.2 Código
- **Rutas escritas a mano:** 44 archivos con rutas `data/…`, 27 con `reports/…`, 25 con `models/…`; cada script arma su ruta (`RAIZ / "data/dataset_v6"`). Mover una carpeta rompe varios scripts a la vez.
- **Utilidades compartidas dentro de scripts versionados:** `f1m`, `ic_f1`, `ic_delta` viven en `evaluation/comparar_v4.py` (importado 9 veces); `mcnemar` en `comparar_modelos.py` (10 veces); la inferencia `probs_propio` en `combinar_modelos.py` (8 veces), que a su vez importa la API (`import app.api.main`) para cargar modelos.
- **Carpetas vacías:** `src/models/` y `src/utils/` solo tienen `__init__.py`.
- **Código fuera de `src/`:** `scripts_hilos/` (3 scripts), `data/hilos_reales/etiquetas/lab1–5.py`.
- **Referencia rota:** `comparar_v4.py` y el notebook de Colab mencionan `data/dataset_v4_e2`, que no existe.
- **Sin pruebas:** no hay `tests/`; la única verificación automática es `build_dataset_final.py --selftest`.

### 1.3 `reports/`, `docs/` y raíz
- `reports/` mezcla Etapa I (informes EDA), Etapa II (`v2_auditoria`, `v3_arquitectura`, `v3_resultados`, `9-12-2026`, `verificacion`, comparativas) y la mejora (`fase3_*`, `fairness*`, `optuna_*`, `v4_*`) al mismo nivel.
- `docs/` igual: rúbrica, guiones, planes, prompts y guía de anotación sin agrupar.
- En la raíz: `README_V3.md` y el PDF de la Etapa II.
- `models/` (local, no versionado, 14 GB): versiones (`v3.x`) mezcladas con experimentos (`candA/B/C`, `student*`) y tres enlaces `sB_*`.

## 2. Estructura objetivo

```
proyecto/
├── README.md · CHANGELOG.md · requirements.txt · Makefile (nuevo)
├── data/
│   ├── README.md                 ← mapa y LINAJE: qué es cada carpeta, de cuál sale y qué script la genera
│   ├── fuentes/
│   │   ├── corpus_etapa1/        (hoy raw/)
│   │   ├── x_oct2026/            (hoy new-10-7-2026/)
│   │   └── hilos_x/              (hoy hilos_reales/crudo + crudo_fase1)
│   ├── anotacion/
│   │   ├── etapa1/               (hoy interim/)
│   │   └── hilos/                (hoy hilos_reales/: ciego/, etiquetas/, sesiones/ ← lab*.py, revision/, predicciones/, REGISTRO.md)
│   ├── dataset/                  ← EL dataset vigente = v1.8.0 (hoy dataset_final; entrena el modelo v3.4.0)
│   ├── historico/                versiones anteriores, solo para reproducir cifras ya reportadas (ver §8)
│   │   ├── VERSIONES.md          tabla versión → qué agregó → modelo que entrenó
│   │   └── v1.0.0/ … v1.7.0/     (hoy processed, dataset_b2, v3, v4, v5a, v5f, v6, v7, archivo/dataset_v8)
│   └── evaluacion/
│       ├── banco_congelado/      ← VIGENTE (MANIFEST.json con SHA-256)
│       └── hard_cases/
├── src/                          SE MANTIENE; solo se agregan:
│   ├── rutas.py                  ← única fuente de rutas (DATASETS, BANCO, REPORTS, MODELS…)
│   ├── evaluation/metricas.py    ← f1m, IC, McNemar (comparar_v4 y comparar_modelos los re-exportan: nada se rompe)
│   ├── models/inferencia.py      ← probs_propio y carga de modelos (combinar_modelos lo re-exporta)
│   ├── data/hilos/               ← scripts_hilos/ (prep, eval1, eval4)
│   └── README.md                 qué es cada subcarpeta (v3 = Etapa II, audit = auditoría 2v, …)
├── app/                          sin cambios (api, ui, pruebas)
├── scripts/                      arrancar_demo.ps1, pipelines
├── tests/                        (nuevo, sin GPU)
├── notebooks/                    sin cambios salvo rutas
├── reports/
│   ├── etapa1/  etapa2/  mejora/ (cada uno con lo que hoy está suelto)
│   └── figures/
├── docs/
│   ├── guia_anotacion.md         (se queda arriba: es la referencia)
│   ├── etapa1/  etapa2/ (+ README_V3, PDF Etapa II, rúbrica, guiones, fe de erratas, cuestionario)
│   ├── mejora/  (plan, estrategia, estado, review, este plan)
│   ├── defensa/ (guion video, impacto social)
│   └── prompts/
├── archivo/                      se queda (snapshot 2026-10-07 y scripts_build); dataset_v8 pasa a data/datasets/
└── models/ (local)               versiones/ (v3.0.0 … v3.4.0) · experimentos/fase3/ (cand*, student*) · MODELOS.md
```

## 3. Decisiones de diseño
1. **Por propósito, no por fecha:** fuentes → anotación → datasets → evaluación sigue el flujo real del proyecto y hace evidente qué entra a entrenar y qué no.
2. **Un solo `src/rutas.py`:** los scripts dejan de escribir rutas; se cambian las cadenas por constantes (`R.DATASETS / "v6"`). Es el único cambio de código masivo y es mecánico.
3. **Compatibilidad hacia atrás:** las utilidades se mueven a módulos propios, pero los módulos viejos las re-exportan (`from src.evaluation.metricas import f1m`) para que ningún import existente falle.
4. **Copias idénticas:** se **mantienen** por ahora (algunos scripts históricos apuntan a ellas). El README de `data/` indica cuáles son idénticas. *(Opcional, ver §7: quedarse con un solo original y que los demás apunten a él.)*
5. **`git mv`** para conservar el historial de cada archivo.

## 4. Fases

| # | Fase | Qué se hace | Riesgo |
|---|---|---|---|
| 0 | Red de seguridad | Etiqueta `pre-reestructura`; generar los valores dorados (§5); crear `tests/` y `Makefile`. | Bajo |
| 1 | `src/rutas.py` | Crear el módulo y reemplazar las rutas literales en los 44 + 27 + 25 archivos, **sin mover nada todavía**. Los dorados deben seguir iguales. | Medio (mecánico) |
| 2 | Mover `data/` | `git mv` a la estructura nueva; ajustar solo `rutas.py`; `data/README.md` con el linaje; regenerar y comparar `MANIFEST.json`. | Medio |
| 3 | Utilidades | `metricas.py` e `inferencia.py` con re-exportación; `scripts_hilos/` → `src/data/hilos/`; `lab*.py` → `data/anotacion/hilos/sesiones/`; `src/README.md`. | Bajo |
| 4 | `reports/` y `docs/` | Agrupar por etapa; mover `README_V3.md` y el PDF de la raíz a `docs/etapa2/`; actualizar enlaces en README y CHANGELOG. | Bajo |
| 5 | `models/` (local) | Separar `versiones/` y `experimentos/`; ajustar manifests (`candC`) y la ruta de la API; quitar los enlaces `sB_*`; `MODELOS.md`. | Bajo |
| 6 | Cierre | README con «cómo reproducir» y mapa del repo; arreglar la referencia rota a `dataset_v4_e2`; CHANGELOG; PR o push. | Bajo |

## 5. Verificación (al terminar cada fase)
**Valores dorados**, generados en la fase 0:
1. `build_dataset_final.py --selftest` en OK y `metadata.json` idéntico (12,641 filas, 0 fugas).
2. SHA-256 del banco congelado y del test oficial iguales a `MANIFEST.json`.
3. `comparar_fase3.py v3.3.0 candC v3.4.0` reproduce la tabla de `reports/fase3_candidatos.md`.
4. La API devuelve exactamente la misma clase y probabilidad para 20 textos fijos.
5. `fairness.py --modelo v3.4.0` produce el mismo informe.
6. `python -m compileall src app` sin errores y una búsqueda de rutas literales `"data/` fuera de `rutas.py` sin resultados.

**Pruebas nuevas (`tests/`, sin GPU, `make test`):** rutas de `rutas.py` existen · dataset final sin fugas · métricas contra valores calculados a mano · normalización v1.2 con casos fijos · re-exportaciones (los imports viejos siguen funcionando).

## 6. Coordinación con el equipo
- Mueve muchos archivos: antes de empezar, Cristian y Julio deben subir lo que tengan pendiente; después, `git pull`.
- Con `git mv` el historial se conserva y los conflictos son menores.
- Esfuerzo estimado: **3–4 horas** (la fase 1 es la más larga).

## 7. Decisiones pendientes
1. **¿Se hace en una rama con PR o directo en `v3`?** Recomiendo rama `reestructura` + PR, porque son ~400 archivos movidos y tus compañeros trabajan en `v3`.
2. **¿Deduplicar las copias idénticas?** Recomiendo **no** por ahora (cero riesgo); se documentan en `data/README.md`. Si se quiere, ahorraría ~20 MB y simplificaría, a cambio de tocar más scripts.
3. **¿Nombres de carpetas en español** (`fuentes`, `anotacion`, `datasets`, `evaluacion`)? Recomiendo sí, coherente con el resto del repo.

## 8. Versionado del dataset (semver propio, separado del modelo)
Hoy las carpetas se llaman `dataset_v3 … v8` y se confunden con las versiones del **modelo** (v3.x.x). Hay **un solo dataset**; las carpetas son fotos suyas en el tiempo. Se versiona con `MAJOR.MINOR.PATCH` propio, escrito como **dataset v1.x.x**:

- **MAJOR:** cambian las clases, la guía de anotación de forma incompatible o la partición val/test (las cifras dejan de ser comparables).
- **MINOR:** se agregan (o quitan) datos de entrenamiento.
- **PATCH:** correcciones sin datos nuevos (normalización, fugas, duplicados, re-etiquetado puntual).

Comprobado: **val (459) y test (460) son los mismos en todas las versiones** (mismos ID, texto, `texto_modelo` y etiqueta), así que todo es MAJOR 1: solo cambió el entrenamiento.

| Dataset | Hoy | Train | Cambio | Modelo que entrenó |
|---|---|---|---|---|
| v1.0.0 | `processed/` | 2,144 | Corpus limpio de la Etapa I | baselines Etapa I |
| v1.1.0 | `dataset_b2/` | 3,293 | Dataset de la Etapa II | mBERT / XLM-R (auditoría 2v) |
| v1.2.0 | `dataset_v3/` | 6,416 | + sintéticos | RoBERTuito Etapa II |
| v1.3.0 | `archivo/…v4_normalizacion_v1.1/dataset_v4` | — | + 4,053 textos de X (oct.), normalización v1.1 | — |
| v1.3.1 | `dataset_v4/` | 10,469 | PATCH: normalización v1.2 y fugas | v3.0.0 (textos de oct. con peso 0) |
| v1.4.0-a | `dataset_v5a/` | 6,749 | Experimento con hilos reservados | ninguno desplegado |
| v1.4.0 | `dataset_v5f/` | 7,199 | + 4 hilos reales + casos difíciles; sin X oct. | v3.1.0 |
| v1.5.0 | `dataset_v6/` | 8,164 | Consenso de 3 anotadores, 9 hilos | v3.2.0-rc1 |
| v1.6.0 | `dataset_v7/` | 8,551 | + hilos con Amenazas | v3.3.0-rc1 |
| v1.7.0 | `archivo/datasets/dataset_v8` | 9,195 | + hilos de Odio (LGBT, racismo) | v3.4.0-rc1 (descartado) |
| **v1.8.0** | `dataset_final/` | **12,641** | Pool completo de la fase 1; banco congelado excluido | **v3.4.0 (vigente)** |

Reglas desde ahora:
1. Solo existe `data/dataset/`; su `metadata.json` lleva `"version": "1.8.0"` y lo genera **un único script** (`build_dataset_final.py`).
2. Cada versión nueva = una entrada en `historico/VERSIONES.md` + una **etiqueta git** `dataset-v1.9.0`; la foto anterior pasa a `historico/`.
3. Cada modelo registra en su `manifest.json`/`metricas.json` la versión del dataset con que se entrenó (`"dataset": "1.8.0"`).
4. `dataset_v7_copia` (copia idéntica de v1.6.0) no se mueve como versión aparte; se anota en `VERSIONES.md`.
