# Rama `v3` — selección de arquitectura, corpus dirigido y resultados finales

**Autor de la rama:** Willian Alexander Chávez Servellón · 12 de septiembre de 2026

Esta rama contiene la tercera iteración del clasificador, la auditoría de la
entrega 2v que la motivó, y todo lo necesario para reproducir ambas.

---

## Resultado

```
F1-macro sobre test.csv (n = 460)   0.8499
IC 95 % bootstrap                   [0.8164, 0.8824]
Accuracy                            0.8522  (392/460)
```

La meta del proyecto era F1-macro ≥ 0.80. Aquí se cumple en el criterio duro:
no pasa solo el punto estimado, pasa también el extremo inferior del intervalo.

| Modelo | F1-macro | IC 95 % | McNemar vs V3 |
|---|---|---|---|
| **V3 (RoBERTuito afinado)** | **0.8499** | [0.8164, 0.8824] | — |
| XLM-R v1 | 0.8058 | [0.7665, 0.8420] | p = 0.0186 |
| XLM-R mitigado (Prototipo V2) | 0.7887 | [0.7486, 0.8257] | p = 0.0011 |
| mBERT B2 | 0.7610 | [0.7172, 0.7983] | p = 0.0000 |

`val` y `test` son byte a byte idénticos a los de B2 (`sha 45aabe9744711d74` y
`5d1284efcc7df20f`), así que las cuatro filas son directamente comparables.

---

## Qué hay aquí

| Ruta | Contenido |
|---|---|
| `reports/9-12-2026/` | Los dos informes en `.md`, `.pdf` y `.docx`: auditoría de la entrega 2v y resultados de la V3 |
| `src/v3/` | Bake-off, generador de sintéticos, ablaciones, HPO, entrenamiento final y evaluación |
| `src/audit/` | Reejecución independiente de los modelos de la 2v, batería adversarial y sonda dirigida |
| `src/features/normalization.py` | Normalizador **v1.2**, con dos correcciones (abajo) |
| `data/dataset_v3/` | Corpus V3: 6,202 de train, `val`/`test` intactos, y los sintéticos con su plantilla de origen |
| `app/api/` · `app/ui/` | Prototipo FastAPI e interfaz web |
| `reports/v3_arquitectura/` | Bake-off, ablaciones y las 20 pruebas de la búsqueda de hiperparámetros |
| `reports/v3_resultados/` | Logits, predicciones y métricas finales |
| `reports/v2_auditoria/` | Artefactos de la auditoría: logits de los cuatro checkpoints anteriores, batería, sonda y prueba de evadibilidad |

**Los pesos no están versionados.** El modelo final pesa 418 MB y GitHub corta
en 100 MB por fichero. Todos los scripts son deterministas con semilla fija, así
que se reconstruye con:

```bash
python3 src/v3/construir_dataset.py
python3 src/v3/hpo.py pysentimiento/robertuito-base-cased robertuito 20
python3 src/v3/entrenar_final.py
python3 src/v3/evaluar.py models/v3/final v3_final
```

El SHA-256 de los pesos de referencia es
`e79618319c7de5c1497f58de99856f701f3daafeee34a5060512c7a0158a1a3a`.

---

## De dónde salió la mejora

1. **Cambiar de familia de modelo (+0.04).** RoBERTuito y TwitterXLM-R están
   preentrenados sobre lenguaje de redes sociales en español; mBERT y XLM-R base
   no. TwitterXLM-R es *la misma arquitectura* que XLM-R base y le saca +0.039
   solo por el corpus de preentrenamiento.
2. **Optimización de hiperparámetros (+0.025).** Veinte pruebas con Optuna sobre
   validación. Nunca se había hecho en el proyecto.
3. **Sintéticos dirigidos con el régimen correcto (+0.01 a +0.02).** Peso
   completo durante el grueso del entrenamiento y tres épocas finales solo con
   ejemplos reales.

Y tres vías que **no** funcionaron, documentadas para que nadie las repita:

- **Escalar el modelo.** XLM-R large (560 M, 42 min) rinde peor que RoBERTuito
  (109 M, 1.5 min).
- **Extender el vocabulario** con los placeholders de emoji y la jerga canónica.
  Perjudica en las seis configuraciones probadas.
- **Generar sintéticos donde no hay problema.** El subconjunto dirigido, con
  1,292 filas menos, empata con el completo.

---

## Correcciones al pipeline compartido

Dos son bugs que afectaban a todo el proyecto:

- **`normalizar()` destruía la ofuscación con arroba.** `m@tar` se convertía en
  `m@usuario`, porque la anonimización de menciones no exigía límite de palabra.
  La ofuscación con arroba es justo una de las evasiones que el sistema debe
  detectar. `test.csv` no cambia ni una fila con el arreglo.
- **🔫 se traducía como `:pistola_de_agua:`.** Es el nombre Unicode vigente, pero
  para esta tarea enseñaba «agua» donde hay un arma. Ahora es `:pistola:`.
- **Siete filas compartidas** entre la batería adversarial y el train quedaron
  fuera. El solape se arrastraba desde agosto.

---

## Datos y privacidad

El corpus son publicaciones públicas de X y Facebook recolectadas manualmente.
Los autores están seudonimizados (`USER_####`) y `texto_modelo` —la columna que
entrena el modelo— tiene las menciones sustituidas por `@usuario`.

**`texto_original` conserva las menciones tal como aparecían en la publicación**,
incluidos handles de cuentas reales. Se mantiene así por decisión del equipo,
para preservar la trazabilidad del dato. Quien reutilice este corpus debería
entrenar sobre `texto_modelo` y tener presente que `texto_original` no está
anonimizado. Las URLs de origen sí quedaron fuera desde el inicio.

El corpus contiene lenguaje ofensivo y discurso de odio explícito por la
naturaleza de la tarea.

---

## Limitaciones

- La brecha entre plataformas persiste: F1 0.8976 en X frente a 0.7773 en
  Facebook. Es composición del corpus, no arquitectura.
- La sonda dialectal sobre datos reales tiene **n = 29**. Un caso mueve la
  métrica 3.4 puntos.
- Los emojis de amenaza (🔫🔪⚰️) siguen sin un solo caso real recolectado: su
  cobertura es enteramente sintética.
- La sonda dirigida de 204 casos **dejó de ser independiente para el modelo V3**:
  cuatro de sus textos están en el train y el 31 % usa el mismo léxico que
  alimentó al generador. La cifra limpia es el 0.8499 sobre `test.csv`, donde el
  solape con el train es 0.
- La dispersión entre semillas es de 1.8 puntos. El modelo publicado es la
  **mediana** de tres semillas, no la mejor.
