# Plan: reentrenar mBERT (Cristian) con el dataset v2.0.0 y usar Argilla para anotar

**Fecha:** 6 de noviembre de 2026 · **Rama:** `v3` · **Dataset:** v2.0.0 (`data/dataset/`)

Este plan revisa y mejora la propuesta anterior. Hay dos objetivos:

1. Reentrenar mBERT con el **mismo contrato** que el resto del equipo, para que las cifras se puedan comparar con v3.4.0 y candB_v2.
2. Usar Argilla para anotar **donde aporta algo que el repo no tiene**, sin crear otro pipeline.

Restricción: crear lo mínimo. **Un solo script nuevo** (`src/data/threads/argilla_io.py`) y cambios pequeños en dos archivos que ya existen. Ningún `.ps1` nuevo, ningún notebook nuevo y ningún formato CSV nuevo para el entrenamiento.

---

## 0. Qué se corrige de la propuesta anterior

| Propuesta anterior | Problema | Corrección |
|---|---|---|
| Argilla como "capa opcional aguas arriba" para etiquetar más datos | Al repo no le faltan etiquetas: tiene 26,011 textos de la ronda 3 con κ = 0.844. Lo que le falta es **validación humana**. `data/dataset/LEEME.md` lo dice: las etiquetas de val_hilos y test_hilos son "consenso de anotadores LLM, sin validación humana", y `consolidado_ronda3.md` advierte que A, B y C son el mismo modelo (errores correlacionados) | El uso principal de Argilla pasa a ser la **validación humana del test principal**. Anotar datos nuevos queda como uso secundario |
| Modo B: "registrar el checkpoint de mBERT en Argilla" | Argilla no aloja ni ejecuta modelos. Solo recibe *suggestions* ya calculadas | Las sugerencias se calculan con `src/models/inference.py → probs_propio()` (el mismo cargador que usa `comparar_v2.py`) y se suben como `rg.Suggestion` |
| Modo C: Argilla como "segundo producto" | No es un producto. Ese modo mezcla despliegue con anotación | Se elimina |
| Volcar el export de Argilla en un `consenso_*.csv` nuevo | Obliga a tocar `build_dataset_final.py` y añade otro formato | El export escribe archivos `salida_<lote><anotador>.csv` (`ID,label`), que es el formato que **ya** lee `src/data/threads/consolidar_ronda3.py`. Para validar la evaluación se escribe un solo CSV nuevo que no entra en ningún entrenamiento |
| "Recomendado: `entrenar_v5` con los hiperparámetros por defecto" | Los valores por defecto (lr 5.7e-5, batch 32) son la receta Optuna **de RoBERTuito**. Para mBERT, un lr tan alto suele ser inestable | Se eligen dos recetas antes de entrenar y se decide entre ellas **solo con val_v2** (sección 2.2) |
| Usar `src/audit/mbert_numpy.py` para la defensa | Es la auditoría del mBERT de la Etapa II (`src/README.md` lo marca como histórico) y no sirve para el modelo nuevo | Basta con `comparar_v2.py`, que ya da IC bootstrap y McNemar |
| Usar `mbert-sv` "con `--solo-banco`" | Es correcto, pero `pipeline_v360.ps1` ya lo hace en su paso 5 | Ya está cubierto. `mbert-sv` solo sirve como referencia histórica |

---

## 1. Lo que ya existe y se reutiliza sin cambios

| Pieza | Archivo | Uso para mBERT o Argilla |
|---|---|---|
| Entrenamiento con pesos por muestra y por clase, 3 semillas, early stopping y guardado HF | `src/train/entrenar_v5.py` (`--modelo_base`) | Entrena mBERT sin código nuevo |
| val_v2 = val oficial + val_hilos normalizado | `scripts/pipeline_v360.ps1`, paso 0 → `runs/val_v2.csv` | El mismo archivo de selección que candB_v2 |
| Inferencia de cualquier carpeta `models/<n>/semilla_*/modelo` | `src/models/inference.py → probs_propio` (carga el tokenizer **desde la carpeta del modelo**, aplica `normalizar()` y usa max_len 128) | Evalúa mBERT y genera las sugerencias para Argilla |
| Evaluador de referencia con los 7 criterios, IC y McNemar | `src/evaluation/comparar_v2.py` | Informe de mBERT |
| Consolidación de anotaciones ciegas A, B y C | `src/data/threads/consolidar_ronda3.py` (lee `blind/ronda3/lote_*.csv` y `salida_<lote>{a,b,c}.csv`) | Destino del export de Argilla cuando hay que desempatar o anotar textos nuevos |
| Constructor del dataset con aborto ante fugas | `src/data/build_dataset_final.py` (+ `--selftest`, `--dry`) | Protege el train de cualquier dato que venga de Argilla |
| Clases y guía | `docs/guia_anotacion.md` | Texto de `guidelines` y etiquetas del dataset en Argilla |

---

## 2. Reentrenamiento de mBERT

### 2.1 Contrato (no negociable, sale de `data/dataset/LEEME.md`)

- Base `bert-base-multilingual-cased`. Usar la variante *cased*, porque la *uncased* quita las tildes.
- Entrena **solo** `data/dataset/train.csv` con `texto_modelo`. `--peso_nuevos 0`, igual que candB_v2.
- Selección (early stopping, receta, semilla y temperatura) **solo** con `runs/val_v2.csv`.
- `max_length 128`. Normalización v1.2 (`normalizar()`) en los hilos y en el banco. `probs_propio` ya la aplica.
- Guardar en `models/mbert_v2/semilla_<s>/modelo` con `--guardar_modelos`.
- Nunca usar test_hilos, test ni el banco para decidir nada.

### 2.2 Recetas: se fijan ahora, antes de entrenar

| Receta | lr | batch | épocas | wd | warmup | Justificación |
|---|---|---|---|---|---|---|
| **M1: Etapa I de mBERT** | 2e-5 | 16 | 4 | 0.01 | 0.1 | Receta con la que mBERT ya funcionó en la Etapa II |
| **M2: receta B** | la de `runs/mejor_b.args` | | | | | "Mismo entrenamiento, distinto backbone": aísla el efecto de la arquitectura frente a candB_v2 |

Los dos usan `--peso_hilos 3.0` y `--peso_sintetico 0.75`, los mismos pesos por muestra que el equipo.

**Regla de decisión, fijada de antemano:** se corre la semilla 42 con M1 y con M2. Gana la receta con mayor `f1_val` en `semilla_42/resumen.json`. Las otras dos semillas (1337 y 2026) se corren solo con la receta ganadora. Para la tesina se reportan las dos recetas en val_v2, para que se vea que la elección no salió del test.

> `runs/mejor_b.args` no está en el repo (`runs/` no se versiona). Se pide a Willian o se reconstruye desde `reports/improvement/optuna_cv_hilo.json`.

### 2.3 Comandos (sin script nuevo)

```powershell
$PY = ".venv\Scripts\python.exe"; $D = "data/dataset"
# Requisito: runs/val_v2.csv (paso 0 de scripts/pipeline_v360.ps1; si no existe, se corre solo ese bloque)

# M1, semilla 42
& $PY src/train/entrenar_v5.py --modelo_base bert-base-multilingual-cased `
  --train $D/train.csv --val runs/val_v2.csv --test $D/test.csv --adv $D/test_adversarial.csv `
  --peso_nuevos 0 --seeds 42 --lr 2e-5 --batch 16 --epocas 4 --wd 0.01 --warmup 0.1 `
  --guardar_modelos --out models/mbert_v2_M1

# M2, semilla 42 (receta B)
$B = (Get-Content runs/mejor_b.args -Raw).Trim().Split(" ")
& $PY src/train/entrenar_v5.py --modelo_base bert-base-multilingual-cased `
  --train $D/train.csv --val runs/val_v2.csv --test $D/test.csv --adv $D/test_adversarial.csv `
  --peso_nuevos 0 --seeds 42 --guardar_modelos --out models/mbert_v2_M2 @B

# Ganadora: completar semillas en la MISMA carpeta (entrenar_v5 reutiliza semilla_42 si ya existe)
& $PY src/train/entrenar_v5.py ... --seeds 42 1337 2026 --out models/mbert_v2_<ganadora>
# Al final se renombra la carpeta ganadora a models/mbert_v2. La perdedora se conserva (su resumen.json va al informe)
```

Implementado como **pasos 6 y 7** de `scripts/pipeline_v360.ps1`: M1 y M2 con semilla 42, elección por `f1_val` (empate: M1), las 3 semillas con la ganadora, registro de la decisión en `models/mbert_v2/eleccion_receta.json` y comparación (con `--humano` si ya existe `validacion_humana.csv`).

`entrenar_v5.py` reanuda por semilla (`if (ds / "probs_test.npy").exists()`). Por eso completar las semillas no repite la 42.

### 2.4 Evaluación (una sola medición)

```powershell
& $PY src/evaluation/comparar_v2.py v3.4.0 mbert_v2 candB_v2 --salida mbert_v2_vs_v340
```

- `mbert_v2` frente a v3.4.0 da los 7 criterios del plan v2.
- `candB_v2` en la misma tabla da la comparación de arquitectura con la misma receta y los mismos datos, que es el resultado central para la tesina de Cristian.
- Salida: `reports/improvement/mbert_v2_vs_v340.{md,json}`. Es el único número de mBERT que se cita.
- Expectativa honesta: `mbert-sv` quedó 0.08 por debajo de v3.4.0 en el banco (`reports/improvement/mbert_sv_vs_v340.md`). El vocabulario de mBERT trocea peor la jerga y los emojis (`src/audit/analisis_tokenizadores.py`). Un resultado "NO se adopta" también vale para la tesina: muestra por qué conviene un modelo preentrenado en español de redes sociales.

### 2.5 Cambio de código mínimo

- `src/train/entrenar_v5.py`, línea 71: el `help` de `--modelo_base` dice "solo para pruebas; no cambiar". Hay que cambiarlo a "backbone HF (por defecto RoBERTuito; mBERT: bert-base-multilingual-cased)". No cambia nada más.
- Opcional: añadir un **paso 6** al final de `scripts/pipeline_v360.ps1` con el mismo patrón `if (-not (Test-Path ...))`, en lugar de crear otro `.ps1`.

---

## 3. Argilla

### 3.1 Para qué se usa, por prioridad

| Prioridad | Uso | Qué resuelve | ¿Cambia el dataset? |
|---|---|---|---|
| **A (principal)** | **Validación humana del test principal**: muestra de test_hilos + val_hilos anotada a ciegas por 2 personas | La debilidad declarada del v2.0.0: el test principal depende de etiquetas LLM correlacionadas. Da κ humano-humano y κ humano-LLM, y permite reportar el F1 sobre etiquetas humanas | **No.** Archivo aparte, solo para informar |
| B | Desempate humano de los 106 textos `sin_consenso` y revisión de los `consenso_c` de Odio y Amenazas (las clases con menor κ: 0.713 y 0.797) | Ruido en las clases raras del train | Sí, genera un dataset nuevo (v2.1.0) que obliga a reentrenar a todos. Se hace una sola vez y con fecha acordada |
| C | Ronda 4 con *model-in-the-loop*: priorizar textos nuevos donde mBERT y v3.4.0 discrepan, con sugerencias visibles | Recolectar mejor los casos difíciles | Sí (v2.x). Solo después de A |

**Recomendación:** hacer A ya, en paralelo con el entrenamiento de mBERT, porque A no depende de mBERT. B y C quedan para después de la comparación.

### 3.2 Muestra para la validación (A), fijada antes de mirar predicciones

- **Todos** los textos de Odio y Amenazas de test_hilos y val_hilos: 28 + 126 + 29 + 132 = **315**.
- Más 300 No Tóxico y 300 Ofensivo estratificados por hilo, con semilla 2026.
- Total **≈ 915 textos**, con 2 anotadores humanos por texto (`TaskDistribution(min_submitted=2)`). Se reparten entre Cristian, Julio y Willian.
- **A ciegas:** sin sugerencias y sin mostrar la etiqueta LLM, para no anclar a los anotadores.
- Metadatos visibles solo para filtrar (`hilo`, `conjunto`), nunca la etiqueta.

### 3.3 Despliegue

- **HF Space privado** con la plantilla de Argilla (gratuito, sin servidor propio) o **Docker local** (`argilla/argilla-quickstart`) si los textos no pueden salir del equipo.
- Workspace `sv`. Un usuario por anotador. Las credenciales van en `.env` (`ARGILLA_API_URL`, `ARGILLA_API_KEY`). Hay que comprobar que `.env` esté en `.gitignore`. `python-dotenv` ya está en `requirements.txt`.
- `requirements.txt`: añadir `argilla>=2.4` en una sección `# --- Anotación (opcional) ---`.

### 3.4 El único script nuevo: `src/data/threads/argilla_io.py`

Tiene dos subcomandos y no lleva lógica de dataset. Solo traduce entre Argilla y los formatos que el repo ya tiene.

```
python src/data/threads/argilla_io.py subir  --tarea validacion            # 3.2 → dataset sv_validacion_v2
python src/data/threads/argilla_io.py subir  --tarea desempate             # 106 sin_consenso + consenso_c de Odio/Amenazas
python src/data/threads/argilla_io.py subir  --tarea ronda4 --sugerir mbert_v2 v3.4.0
python src/data/threads/argilla_io.py bajar  --tarea validacion            # → labels/validacion_humana.csv
python src/data/threads/argilla_io.py bajar  --tarea desempate|ronda4      # → blind/<ronda>/lote_<L>.csv + salida_<L>{a,b,c}.csv
```

Esqueleto (Argilla SDK 2.x):

```python
import argilla as rg
CLASES = ["No Tóxico", "Lenguaje Ofensivo", "Discurso de Odio", "Amenazas/Violencia"]   # mismo orden que el repo
settings = rg.Settings(
    guidelines=(RAIZ / "docs/guia_anotacion.md").read_text(encoding="utf-8"),
    fields=[rg.TextField(name="texto")],
    questions=[rg.LabelQuestion(name="label", labels={str(i): c for i, c in enumerate(CLASES)})],
    metadata=[rg.TermsMetadataProperty(name="hilo"), rg.TermsMetadataProperty(name="conjunto")],
    distribution=rg.TaskDistribution(min_submitted=2))
# subir: rg.Record(id=ID, fields={"texto": texto_original}, metadata={...}, suggestions=[...] solo en ronda4)
#        sugerencias = probs_propio(f"models/{m}", textos) → rg.Suggestion("label", str(argmax), score=max, agent=m)
# bajar: for r in ds.records(with_responses=True): respuestas "submitted" de r.responses["label"]
```

**Formatos de salida (ninguno es nuevo para el pipeline de entrenamiento):**

- `validacion`: `data/annotation/threads/labels/validacion_humana.csv`, con columnas `ID,conjunto,hilo,label_llm,h1,h2,label_humano`. `label_humano` = h1 si h1 = h2; si no, -1. **No lo lee `build_dataset_final.py`**, así que no puede entrar al train.
- `ronda4`: `lote_<L>.csv` (`ID,texto`) más `salida_<L>a.csv` y `salida_<L>b.csv` (`ID,label`, un archivo por voto humano), y `salida_<L>c.csv` si hay un tercero. Es exactamente lo que `consolidar_ronda3.py` ya valida y consolida.
- `desempate`: el lote se nombra `R3C_H01`, que sigue la convención existente de lotes de desempate (`R3C_`). Solo se escribe `salida_R3C_H01c.csv`: la respuesta humana entra como **C** cuando los dos humanos coinciden (si no coinciden, el texto conserva la C del LLM). No se escriben `a` ni `b`, porque sobrescribirían las etiquetas A y B del LLM. El lote se lee después de `R3C_00x`, así que C humano reemplaza a C LLM y el consolidado vuelve a decidir por mayoría de 3 sin cambiar código.
  - Antes de ejecutarlo, hay que anotar en `REGISTRO.md` que C pasa a ser humano en esos lotes, porque cambia la interpretación de `d`.

### 3.5 Cómo vuelve el resultado al proyecto

**Validación (A).** Se añade un flag opcional `--humano` a `comparar_v2.py`, unas 6 líneas. Si existe `validacion_humana.csv`, el flag agrega a la tabla:
- κ humano-humano y κ humano-LLM (`sklearn.metrics.cohen_kappa_score`, que ya se usa en `consolidar_ronda3.py`);
- F1-macro de cada modelo sobre el subconjunto con `label_humano ≥ 0`.

Esto no cambia el test principal ni los 7 criterios. Es una fila de robustez.

**Desempate y ronda 4 (B y C).** El orden es fijo:

```
argilla_io bajar → consolidar_ronda3.py → build_dataset_final.py --dry (revisar composición)
→ build_dataset_final.py → auditar_dataset.py → subir DATASET_VERSION en src/paths.py y documentar en data/history/VERSIONS.md
→ reentrenar TODOS los modelos que se vayan a comparar
```

`build_dataset_final.py` ya aborta si un texto de val, test, val_hilos, test_hilos, la batería o el banco entra al train, así que el riesgo de fuga desde Argilla queda cubierto sin código nuevo. Si la ronda 4 trae otra carpeta de fuentes, hay que añadir su ruta a `consolidar_ronda3.py` y a `ronda3()` en el constructor. Es un cambio de configuración, no un pipeline nuevo.

---

## 4. Orden de trabajo

```
Semana 1 ─┬─ Cristian: M1 y M2 con semilla 42 (GPU) → elegir receta por val_v2 → semillas 1337 y 2026
          └─ Willian: desplegar Argilla + argilla_io.py "subir --tarea validacion"
                      Equipo (3 personas): anotar ≈ 915 textos a ciegas, 2 votos cada uno
Semana 2 ─┬─ comparar_v2.py v3.4.0 mbert_v2 candB_v2 --salida mbert_v2_vs_v340
          ├─ argilla_io.py "bajar --tarea validacion" → comparar_v2 --humano (κ y F1 humano)
          └─ Decidir si B (desempate) vale un dataset v2.1.0. Si se hace, se reentrena todo
Después  ─── C (ronda 4 con sugerencias de mbert_v2 y v3.4.0), solo si hay tiempo y datos nuevos
```

## 5. Entregables para la tesina de Cristian

| Entregable | Origen |
|---|---|
| Tabla mBERT vs v3.4.0 vs candB_v2: F1 principal con IC, recall por clase, FPR, FPR por jerga, test oficial, McNemar | `reports/improvement/mbert_v2_vs_v340.md` |
| Elección de receta (M1 vs M2) solo con val_v2 | `models/mbert_v2_M*/semilla_42/resumen.json` |
| Fiabilidad de las etiquetas: κ humano-humano, κ humano-LLM y F1 sobre etiquetas humanas | `validacion_humana.csv` + `comparar_v2 --humano` |
| Robustez: batería de 144 | `models/mbert_v2/metricas.json → bateria_144` |
| Pesos | `models/mbert_v2/semilla_*/modelo` (opcional: `scripts/subir_hf.ps1` a un repo HF privado) |

## 6. Inventario de cambios

| Tipo | Archivo |
|---|---|
| Nuevo | `src/data/threads/argilla_io.py` (un script con dos subcomandos) |
| Nuevo (dato) | `data/annotation/threads/labels/validacion_humana.csv`, `models/mbert_v2/`, `reports/improvement/mbert_v2_vs_v340.{md,json}` |
| Modificado | `src/train/entrenar_v5.py` (un `help`), `src/evaluation/comparar_v2.py` (flag `--humano`), `requirements.txt` (una línea) |
| Opcional | Paso 6 en `scripts/pipeline_v360.ps1`; una entrada en `data/annotation/threads/REGISTRO.md` |
| **No** se crea | Ningún `.ps1` nuevo, ningún notebook, ningún constructor de dataset, ningún formato de consenso nuevo |

## 7. Riesgos

1. **Anclaje:** si en la validación (A) se muestran sugerencias o la etiqueta LLM, el κ humano-LLM sale inflado. Por eso A va a ciegas.
2. **Elegir con el test:** usar test_hilos para elegir entre M1 y M2 invalida la comparación. La regla de la sección 2.2 lo impide.
3. **Dataset que se mueve:** hacer B a mitad de la comparación deja a mBERT y a candB_v2 con datasets distintos. B se hace después y obliga a reentrenar todo.
4. **Privacidad:** son textos públicos de X sin usuarios, pero un HF Space público los expone. El Space tiene que ser privado.
5. **Mismo F1 con dos fuentes:** el número oficial siempre sale de `comparar_v2.py`. Las métricas que muestra la interfaz de Argilla no se citan.
