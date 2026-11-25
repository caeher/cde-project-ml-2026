---
language:
- es
license: apache-2.0
base_model: pysentimiento/robertuito-base-cased
pipeline_tag: text-classification
library_name: transformers
tags:
- text-classification
- hate-speech
- toxicity
- spanish
- el-salvador
- robertuito
metrics:
- f1
model-index:
- name: robertuito-toxicidad-sv
  results:
  - task:
      type: text-classification
      name: Toxicidad y discurso de odio (español salvadoreño)
    dataset:
      name: Banco congelado (4 hilos reales de X, n = 1,391)
      type: custom
    metrics:
    - type: f1
      value: 0.720
      name: F1-macro
  - task:
      type: text-classification
      name: Toxicidad y discurso de odio (español salvadoreño)
    dataset:
      name: Test oficial (Etapa I, n = 460)
      type: custom
    metrics:
    - type: f1
      value: 0.832
      name: F1-macro
---

# RoBERTuito-Toxicidad-SV (v3.4.0)

Clasificador de toxicidad y discurso de odio para publicaciones de X y Facebook en el contexto salvadoreño. Es un solo RoBERTuito (`pysentimiento/robertuito-base-cased`, 109 M parámetros) destilado de un ensamble de 6 modelos, con hiperparámetros elegidos por Optuna y validación cruzada por hilo.

Trabajo de graduación, Curso de Especialización en Machine Learning, Escuela de Ingeniería de Sistemas Informáticos, Facultad de Ingeniería y Arquitectura, Universidad de El Salvador (2026). Equipo: Cristian Antonio Escalante Hernández, Julio Enrique De La Quadra Mata y Willian Alexander Chávez Servellón.

## Clases

| id | Clase | Criterio |
|---|---|---|
| 0 | No Tóxico | Sin insulto, ataque ni agresión |
| 1 | Lenguaje Ofensivo | Insulto o vulgaridad sin un grupo protegido de por medio |
| 2 | Discurso de Odio | Ataque a una persona por pertenecer a un grupo protegido |
| 3 | Amenazas/Violencia | Amenaza, incitación, deseo o celebración de daño físico |

Precedencia: Amenazas/Violencia > Discurso de Odio > Lenguaje Ofensivo > No Tóxico.

## Resultados

**Banco congelado** (n = 1,391): 4 hilos reales de X (migrantes, fútbol y política, militares y pandilleros, xenofobia), etiquetados por consenso de 3 anotadores. Ningún modelo del proyecto los vio al entrenar.

| Métrica | Valor |
|---|---|
| F1-macro | 0.720 [IC 95 % 0.687, 0.754] |
| Recall por clase (NT / OF / OD / AM) | 0.888 / 0.813 / 0.669 / 0.470 |
| Tasa de falsos positivos (No Tóxico marcado tóxico) | 0.112 |
| AUROC tóxico vs. no tóxico | 0.939 |

**Test oficial** (n = 460, solo Etapa I): F1-macro 0.832 (X 0.865, Facebook 0.761).

**Sonda de groserías afectivas salvadoreñas**: 18 de 20 groserías afectivas clasificadas como No Tóxico y 17 de 18 insultos detectados.

## Uso

El modelo espera el texto pasado por el normalizador del proyecto (`normalization.py`, incluido en este repositorio): Unicode NFC, @menciones y URLs a marcadores, emojis a texto en español. No pasa a minúsculas ni quita tildes. Las probabilidades se calibran con temperatura T = 1.582, ajustada en validación.

```python
# pip install transformers torch emoji
import numpy as np, torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForSequenceClassification

REPO = "USUARIO/robertuito-toxicidad-sv"
import importlib.util
spec = importlib.util.spec_from_file_location("normalization", hf_hub_download(REPO, "normalization.py"))
norm = importlib.util.module_from_spec(spec); spec.loader.exec_module(norm)

tok = AutoTokenizer.from_pretrained(REPO)
model = AutoModelForSequenceClassification.from_pretrained(REPO).eval()
T = 1.582

def predecir(texto):
    enc = tok(norm.normalizar(texto), truncation=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        z = model(**enc).logits[0].double().numpy() / T
    p = np.exp(z - z.max()); p /= p.sum()
    return {model.config.id2label[i]: round(float(v), 4) for i, v in enumerate(p)}

print(predecir("Qué onda maje, hace años que no te veía"))
```

## Entrenamiento

- Datos: dataset del proyecto v1.8.0 (12,641 filas). Incluye publicaciones reales de X y Facebook de la Etapa I, respuestas de hilos públicos de X etiquetadas por consenso de anotadores, casos difíciles y textos sintéticos dirigidos (ofuscación, emojis, jerga).
- Profesor: ensamble de 6 RoBERTuito (2 recetas × 3 semillas). Estudiante: 1 RoBERTuito con pérdida α·T²·KL + (1 − α)·CE, con α = 0.5 y T = 1.
- Hiperparámetros (Optuna, 12 pruebas, CV por hilo): lr 3.92e-5, 4 épocas, weight decay 0.0060, warmup 0.116, max_length 128, batch 32, pesos de clase con Odio y Amenazas × 1.91.
- Hardware: una GPU de 8 GB.

## Limitaciones y uso responsable

- **No es un moderador autónomo.** Está pensado como apoyo a la revisión humana.
- **Amenazas implícitas:** detecta menos de la mitad de las celebraciones de violencia del tipo «merecen eso y más» (recall 0.47).
- **Sesgo por jerga:** marca como tóxico el 38 % de los textos no tóxicos con jerga salvadoreña del test oficial (n = 29), frente al 7 % sin jerga.
- **Facebook:** rinde unos 10 puntos menos de F1 que en X.
- Las etiquetas de los hilos son consenso de Cristian, Willian y Julio (dos ciegos + desempate).
- El corpus contiene lenguaje ofensivo explícito por la naturaleza de la tarea. Los usuarios están seudonimizados y no se publican datos personales.
