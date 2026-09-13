# Detección de Toxicidad y Discurso de Odio en Redes Sociales — El Salvador

Trabajo de Fin de Máster / Especialización — Universidad de El Salvador, Facultad de Ingeniería y Arquitectura, Escuela de Sistemas Informáticos.

**Equipo:** Julio Enrique De La Quadra Mata · Cristian Antonio Escalante Hernández · Willian Alexander Chávez Servellón

---

## Problema

En El Salvador, X y Facebook concentran buena parte del debate público, pero no existen herramientas de detección de toxicidad adaptadas al registro lingüístico local (modismos, voseo, sarcasmo, leetspeak, emojis con carga discriminatoria). Los modelos genéricos en español fallan ante este dialecto.

## Objetivo general

Desarrollar un sistema de clasificación automática de toxicidad y discurso de odio en publicaciones de X y Facebook del contexto salvadoreño, mediante *fine-tuning* de modelos multilingües (**mBERT** y **XLM-R**), alcanzando **F1-macro > 80%**.

## Taxonomía

| ID | Clase | Criterio |
|---|---|---|
| 0 | No Tóxico | Sin insulto, ataque ni agresión |
| 1 | Lenguaje Ofensivo | Insulto o vulgaridad sin grupo protegido de por medio |
| 2 | Discurso de Odio | Ataque a una persona por pertenecer a un grupo protegido |
| 3 | Amenazas/Violencia | Amenaza, incitación, deseo o celebración de daño físico |

Precedencia: `Amenazas/Violencia > Discurso de Odio > Lenguaje Ofensivo > No Tóxico`. Definiciones operativas y casos límite en [`docs/guia_anotacion.md`](docs/guia_anotacion.md).

---

## Estado del dataset

**3,063 publicaciones** listas para entrenar, estratificadas por clase y plataforma.

| Clase | n | % | vs mínimo 480 | vs alta precisión 771 |
|---|---|---|---|---|
| Lenguaje Ofensivo | 1,060 | 34.6 | cumple | cumple |
| No Tóxico | 815 | 26.6 | cumple | cumple |
| Discurso de Odio | 632 | 20.6 | cumple | faltan 139 |
| Amenazas/Violencia | 556 | 18.2 | cumple | faltan 215 |

Splits: `train` 2,144 · `val` 459 · `test` 460. Balance de plataforma ~50/50 en los tres. Sin solapamiento de IDs ni de textos.

### Hallazgos que condicionan el modelado

1. **X y Facebook son distribuciones distintas** (χ² = 145.1, p < 10⁻³⁰; V de Cramér 0.216). Hay domain shift interno: obliga a estratificar y a reportar métricas desagregadas por plataforma.
2. **Lift de toxicidad asociado a jerga salvadoreña: 1.81x.** Riesgo de que el modelo aprenda el atajo «modismo local → tóxico». Debe medirse en el informe de *fairness*.
3. **La mediana de longitud es mayor en X (20 palabras) que en Facebook (12)**, al revés de lo que asume el perfil del proyecto. Conviene corregirlo en la tesina.

### Piso de referencia sin modelo

Calculado de la pura distribución de clases, sin entrenar nada:

| Estrategia trivial | F1-macro |
|---|---|
| Azar estratificado | 0.250 |
| Azar uniforme | 0.246 |
| Clase mayoritaria | 0.129 |

Frente al objetivo de 0.80 quedan **0.55 puntos** que solo pueden salir de aprender del texto. Que el mayoritario rinda *peor* que el azar es justo lo que penaliza el F1-macro: acierta mucho en una clase y cero en las otras tres.

> **Alcance.** Precisión, *recall* y F1 son métricas de predicción: requieren un modelo entrenado. Pertenecen a la fase de **Modelado** de CRISP-DM, no al EDA. Las únicas cifras de F1 en el informe de EDA son los pisos triviales de arriba. El notebook incluye un baseline clásico entrenado como **Anexo A**, fuera del alcance de ese documento.

---

## Criterio de preparación: preservación máxima

No se aplica preprocesamiento clásico de PLN. Se conservan **tildes, mayúsculas, puntuación y la ortografía original**, porque:

- mBERT y XLM-R fueron preentrenados sobre español real; el tokenizador subword ya modela esas formas.
- La deformación ortográfica (`pvto`, `4güevo`) es evasión deliberada de moderación: es señal, no ruido.
- En producción la API recibirá texto crudo. Normalizar en entrenamiento y no en inferencia produce *train/serve skew*.

Sí se normaliza lo no lingüístico: Unicode NFC, caracteres invisibles, colapso de espacios, placeholders para menciones y URLs, y **demojización a español** (`🤡` → `:cara_de_payaso:`, porque el vocabulario de mBERT casi no cubre emojis).

La pipeline vive en [`src/features/normalization.py`](src/features/normalization.py) y es la **misma función** que debe usar el endpoint de FastAPI.

Cada split trae tres variantes de texto:

| Campo | Uso |
|---|---|
| `texto_modelo` | Entrenamiento y producción. **Campo por defecto.** |
| `texto_agresivo` | Grupo de control del estudio de ablación |
| `texto_original` | Trazabilidad y análisis de errores |

---

## Configuración recomendada para el *fine-tuning*

```python
modelos      = ["bert-base-multilingual-cased", "xlm-roberta-base"]
campo_texto  = "texto_modelo"
num_labels   = 4
max_length   = 128          # cubre sobre el p99; la atención escala O(n²)
padding      = "dinámico"   # DataCollatorWithPadding
batch_size   = 16
lr           = 2e-5         # rango de búsqueda 1e-5 a 5e-5
epochs       = 3-5          # early stopping sobre F1-macro en val
loss         = CrossEntropyLoss(weight=pesos_clase)
```

> **Usar la variante `cased` de mBERT.** La `uncased` aplica `strip_accents=True` y destruye las tildes dentro del propio tokenizador.

Pesos de clase (calculados solo sobre `train`, en `data/processed/metadata.json`):

| Clase | Peso |
|---|---|
| Amenazas/Violencia | 1.3779 |
| Discurso de Odio | 1.2099 |
| No Tóxico | 0.9404 |
| Lenguaje Ofensivo | 0.7224 |

---

## Estructura

```
.
├── data/
│   ├── raw/          # Originales, inmutables
│   ├── interim/      # Intermedios (no versionados)
│   ├── processed/    # train / val / test / corpus_limpio / metadata.json
│   └── external/     # HatEval, Spanish Hate Speech Superset, DETOXIS, CLANDESTINO
├── docs/
│   ├── guia_anotacion.md          # Taxonomía y casos límite
│   ├── perfil_de_trabajo_TFM.pdf
│   ├── etapa-1/                   # Informe Etapa I, dimensionamiento, riesgos
│   └── etapa-2/                   # Rúbrica
├── notebooks/
│   ├── 01_eda_y_limpieza.ipynb            # Auditoría inicial y criterio de normalización
│   └── 02_eda_y_preparacion_final.ipynb   # EDA definitivo y splits (+ Anexo A: baseline)
├── src/
│   ├── data/label_mapping.py       # Taxonomía y mapeo de etiquetas
│   ├── features/normalization.py   # Pipeline única (entrenamiento + inferencia)
│   ├── models/ · evaluation/ · utils/
├── models/           # Checkpoints (no versionados)
├── reports/
│   ├── Informe_EDA_y_Preparacion_de_Datos.pdf   # Criterio de normalización
│   ├── Informe_EDA_para_FineTuning.pdf          # EDA definitivo
│   └── figures/
└── app/
    ├── api/          # FastAPI
    └── ui/           # Dashboard
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/02_eda_y_preparacion_final.ipynb
```

## Siguientes pasos

1. Descargar y armonizar los datasets públicos en `data/external/` con `armonizar_externo()` (notebook 02, sección 9).
2. Ejecutar las celdas de tokenización con acceso a Hugging Face y confirmar `max_length`.
3. *Fine-tuning* en dos etapas: datos públicos, luego corpus salvadoreño (*domain adaptation*). Comparar contra el baseline clásico del Anexo A.
4. Reportar F1-macro global **y desagregado por plataforma**.
5. Ablación `texto_modelo` vs `texto_agresivo` en ambos modelos.
6. Generalización cruzada: entrenar en X, evaluar en Facebook, y viceversa.
7. *Fairness*: medir si la jerga local dispara falsos positivos.

## Requisitos de la Etapa II (rúbrica, 100 pts)

| Criterio | Pts | Estado |
|---|---|---|
| Optimización de hiperparámetros | 20 | Pendiente |
| Modelos avanzados y ensemble | 20 | Pendiente |
| Evaluación rigurosa (CV + test set) | 15 | Splits listos; baseline en Anexo A |
| Análisis de sesgos y ética (fairness) | 15 | Riesgo identificado y cuantificado |
| Prototipo funcional y desplegado | 15 | Pendiente |
| Impacto social y recomendaciones | 15 | Pendiente |

## Consideraciones éticas

Los datos se recolectaron por captura manual de publicaciones públicas, cumpliendo los términos de servicio de las plataformas. Los usuarios están seudonimizados y las URLs de origen quedan fuera del dataset publicable (contienen el *handle* real de la cuenta). El corpus contiene lenguaje ofensivo y discurso de odio explícito por la naturaleza de la tarea de investigación.
