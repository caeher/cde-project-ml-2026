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
      name: Test principal (hilos apartados + banco congelado, n = 3,366)
      type: custom
    metrics:
    - type: f1
      value: 0.752
      name: F1-macro
  - task:
      type: text-classification
      name: Toxicidad y discurso de odio (español salvadoreño)
    dataset:
      name: Test oficial (Etapa I, n = 460)
      type: custom
    metrics:
    - type: f1
      value: 0.827
      name: F1-macro
---

# RoBERTuito-Toxicidad-SV (v3.6.0)

Clasificador de toxicidad y discurso de odio para publicaciones de X y Facebook en el contexto salvadoreño. Es un solo RoBERTuito (`pysentimiento/robertuito-base-cased`, 109 M parámetros) destilado de un ensamble de 3 modelos, entrenado con el dataset del proyecto v2.0.0 (20,028 textos).

Trabajo de graduación, Curso de Especialización en Machine Learning, Escuela de Ingeniería de Sistemas Informáticos, Facultad de Ingeniería y Arquitectura, Universidad de El Salvador (2026). Equipo: Cristian Antonio Escalante Hernández, Julio Enrique De La Quadra Mata y Willian Alexander Chávez Servellón.

La versión anterior (v3.4.0) está disponible en la etiqueta `v3.4.0` de este repositorio.

## Clases

| id | Clase | Criterio |
|---|---|---|
| 0 | No Tóxico | Sin insulto, ataque ni agresión (incluye groserías afectivas: «qué onda maje») |
| 1 | Lenguaje Ofensivo | Insulto o vulgaridad sin un grupo protegido de por medio |
| 2 | Discurso de Odio | Ataque a una persona por pertenecer a un grupo protegido |
| 3 | Amenazas/Violencia | Amenaza, incitación, deseo o celebración de daño físico, explícita o implícita |

Precedencia: Amenazas/Violencia > Discurso de Odio > Lenguaje Ofensivo > No Tóxico.

## Resultados

**Test principal** (n = 3,366): 18 hilos reales de X apartados del entrenamiento (amenazas, fútbol y humor, política) más el banco congelado de 4 hilos (migrantes, fútbol y política, militares y pandilleros, xenofobia). Ningún texto, ni ningún hilo, estuvo en el entrenamiento.

| Métrica | v3.6.0 | v3.4.0 (anterior) |
|---|---|---|
| F1-macro [IC 95 %] | **0.752** [0.728, 0.774] | 0.708 [0.683, 0.731] |
| Exactitud | 0.859 | 0.835 |
| F1 por clase (NT / OF / OD / AM) | 0.916 / 0.812 / 0.577 / 0.705 | 0.902 / 0.783 / 0.566 / 0.581 |
| Recall por clase (NT / OF / OD / AM) | 0.911 / 0.827 / 0.595 / 0.679 | 0.903 / 0.786 / 0.614 / 0.539 |
| Falsos positivos (No Tóxico marcado tóxico) | **0.089** | 0.097 |
| Tóxicos no detectados | 0.141 | 0.177 |
| AUROC tóxico vs. no tóxico | 0.952 | 0.940 |
| ECE (tras calibrar) | 0.024 | 0.043 |

**Test oficial** (n = 460, solo Etapa I): F1-macro 0.827 [0.791, 0.861] (X 0.857, Facebook 0.757).

**Sonda de groserías afectivas**: 17 de 20 groserías afectivas como No Tóxico y 18 de 18 insultos detectados.

## Uso

El modelo espera el texto pasado por el normalizador del proyecto (`normalization.py`, incluido aquí): Unicode NFC, @menciones y URLs a marcadores, emojis a texto en español. No pasa a minúsculas ni quita tildes. Las probabilidades se calibran con temperatura T = 1.415, ajustada en validación.

```python
# pip install transformers torch emoji
import importlib.util, numpy as np, torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForSequenceClassification

REPO = "USUARIO/robertuito-toxicidad-sv"
spec = importlib.util.spec_from_file_location("normalization", hf_hub_download(REPO, "normalization.py"))
norm = importlib.util.module_from_spec(spec); spec.loader.exec_module(norm)

tok = AutoTokenizer.from_pretrained(REPO)
model = AutoModelForSequenceClassification.from_pretrained(REPO).eval()
T = 1.415

def predecir(texto):
    enc = tok(norm.normalizar(texto), truncation=True, max_length=128, return_tensors="pt")
    with torch.no_grad():
        z = model(**enc).logits[0].double().numpy() / T
    p = np.exp(z - z.max()); p /= p.sum()
    return {model.config.id2label[i]: round(float(v), 4) for i, v in enumerate(p)}

print(predecir("Qué onda maje, hace años que no te veía"))
```

## Entrenamiento

- **Datos:** dataset del proyecto v2.0.0 (20,028 textos: 8,914 No Tóxico, 5,453 Ofensivo, 2,876 Odio, 2,785 Amenazas). Publicaciones reales de X y Facebook de la Etapa I, respuestas de hilos públicos de X etiquetadas por consenso de anotadores (guía v2.0) y textos sintéticos dirigidos (ofuscación, emojis, jerga). Partición por hilos: ningún hilo de validación o test aparece en el entrenamiento.
- **Profesor:** 3 RoBERTuito (semillas 42, 1337, 2026) con la receta elegida por Optuna (validación cruzada por hilo).
- **Estudiante:** 1 RoBERTuito con pérdida α·T²·KL + (1 − α)·CE, α = 0.5, T = 1; semilla 42 elegida por F1 en validación (0.802).
- **Hiperparámetros:** lr 3.92e-5 · 4 épocas · batch 32 · weight decay 0.0060 · warmup 0.116 · max_length 128 · peso de hilos 1.53 · pesos de clase con Odio y Amenazas × 1.91 · early stopping (paciencia 2) sobre F1-macro.
- **Hardware:** una GPU NVIDIA RTX 4060 Laptop de 8 GB; unos 30 minutos el profesor y 12 minutos por semilla del estudiante.

## Limitaciones y uso responsable

- **No es un moderador autónomo.** Está pensado como apoyo a la revisión humana.
- **Discurso de Odio** es la clase más débil (recall 0.595): hay pocos ejemplos reales de odio en los hilos nuevos.
- **Jerga salvadoreña:** en hilos nuevos marca como tóxico el 4.3 % de los textos inofensivos con jerga (n = 47), pero en el test oficial sigue en 38 % (n = 29).
- **Facebook:** rinde unos 10 puntos menos de F1 que en X.
- Las etiquetas de los hilos son consenso entre Cristian, Willian y Julio (dos anotadores ciegos + desempate del tercero).
- El corpus contiene lenguaje ofensivo explícito por la naturaleza de la tarea. No se publican usuarios, menciones ni enlaces.
