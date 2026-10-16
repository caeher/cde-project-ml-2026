Copiar desde la línea siguiente y pegarlo como primer mensaje del chat nuevo, con la carpeta `proyecto` conectada.

---

Hola. Soy Willian Chávez, estudiante de maestría en la Universidad de El Salvador. Vamos a continuar un proyecto que ya tiene mucho avance. Antes de hacer nada, leé completo `docs/Review_del_Proyecto.md`: ahí está la historia, las cifras verificadas, los errores conocidos y los pendientes. Después leé `docs/guia_anotacion.md` y `data/dataset_v4/README.md`.

## El proyecto

Clasificación automática de toxicidad en publicaciones salvadoreñas de X y Facebook, en 4 clases exactas: 0 No Tóxico · 1 Lenguaje Ofensivo · 2 Discurso de Odio · 3 Amenazas/Violencia. La meta es F1-macro ≥ 0.80 sobre test, con el extremo inferior del IC 95 %. El equipo somos Cristian Escalante, Julio De La Quadra y yo; mi rol es datos, normalización, auditoría y estadística.

El sistema actual (Etapa II) es RoBERTuito en ensemble de 3 semillas: **F1-macro 0.8529, IC [0.8191, 0.8858]**, entrenado sobre 6,416 filas (2,144 reales y el resto sintéticas). Ese entrenamiento vive en el repo del equipo, github.com/caeher/cde-project-ml-2026, rama v3; no está en esta carpeta.

## Dónde quedamos

El 7 de octubre agregamos 4,328 textos reales de X (`data/new-10-7-2026/`). Ya están limpios en `data/dataset_v4/` por `src/data/build_dataset_v4.py`:

- Se quitaron 80 que estaban en val/test, conflictos entre anotadores y duplicados.
- Se reetiquetaron 384 insultos políticos de Odio a Ofensivo, por la regla de la guía.
- Quedaron 4,074 incorporadas.

Con un proxy lineal, los datos nuevos son neutrales en total: **mejoran X (+2.2) y empeoran Facebook (−4.8)**. Falta reentrenar RoBERTuito de verdad. El script está listo en `src/train/entrenar_v4.py`, pero tu entorno no tiene GPU ni torch, así que el entrenamiento va en Colab.

## Lo que necesito ahora

1. Armar un **notebook de Colab** (`.ipynb`) autocontenido que:
   - instale las dependencias;
   - construya el dataset con `build_dataset_v4.py --base <train de 6,416 de la Etapa II>` (yo subo ese archivo);
   - entrene con `entrenar_v4.py` dos veces: con los datos nuevos y con `--peso_nuevos 0.0` como línea base, mismas semillas;
   - imprima al final la tabla comparativa: F1 con IC, F1 por plataforma, FPR con y sin jerga, batería de 144 por grupo y McNemar entre ambas corridas.
2. Cuando te traiga los resultados (`metricas.json` y `preds_test.csv`), ayudarme a decidir si adoptamos el modelo v4, con evidencia estadística y no por la cifra puntual.
3. Después: corregir los 3 errores graves del reporte de la Etapa II, listados en la sección 3 del review.

## Reglas de trabajo que ya acordamos

- **val (459) y test (460) no se tocan nunca.** Verificar siempre que ningún texto de train coincida con val, test o la batería adversarial.
- **Reproducir, no creer:** toda cifra se recalcula desde predicciones o pesos, no se copia de un informe.
- Con n = 460, diferencias de 2–3 puntos pueden ser ruido. Toda comparación lleva McNemar pareado y bootstrap.
- La afiliación política no es grupo protegido. «Marero» tampoco.
- No usar reglas post-hoc (regex, umbrales manuales que solo empujan a No Tóxico): ya demostramos que se evaden.
- Usá una sola normalización: `src/features/normalization.py`.
- Respondeme en español, directo y sin relleno. Si algo no se midió, decilo; no estimes.
