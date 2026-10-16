# Estrategia de mejora del modelo (10 de octubre de 2026)

## Diagnóstico (medido, no supuesto)
El modelo final (RoBERTuito, 5 semillas) rinde F1-macro 0.8499 en el test oficial, pero en **hilos reales de X que nunca vio** (4 hilos, 716 respuestas etiquetadas con la guía v2.0, ver `data/annotation/threads/`) rinde mucho peor:

| Hilo | n | Acierto | F1-macro | Fallo principal |
|---|---|---|---|---|
| Repatriados venezolanos | 119 | 58.0 % | — | falsos positivos sobre No Tóxico (críticas duras y sarcasmo) |
| Canje humanitario | 170 | 73.5 % | — | — |
| Invasión | 180 | 53.3 % | 0.476 | 66 de 120 No Tóxico marcados como tóxicos |
| Feminismo | 247 | 47.8 % | 0.356 | **misoginia**: detecta 2 de 32 textos de Odio |

Debilidades concretas: (1) misoginia y sexismo sin insulto explícito → clasificados Ofensivo; (2) amenazas implícitas («le llega su hora», «con machetes») → No Tóxico; (3) modismos con «matar» y groserías de celebración → falsos positivos; (4) insultos regionales («veneco») → subdetectados; (5) tono hostil de un hilo contagia a mensajes neutros (falsos positivos sobre No Tóxico).

## Estrategia
1. **Datos nuevos de dominio, no sintéticos de plantilla.** Hilos reales de X (BrowserOS neo) y pares mínimos escritos a mano con variedad (`data/evaluation/hard_cases/`). Los pares comparten superficie y cambian de clase, de modo que la señal es el contenido y no una palabra suelta.
2. **Prevenir atajos.** Los sintéticos de plantilla ya produjeron atajos (emoji ⇒ ofensivo, «te voy a» ⇒ amenaza). Aquí cada fila nueva es real o un par mínimo; ninguna viene de plantilla repetida.
3. **Prevenir memorización y fugas.** Split **por hilo** (no por mensaje): la variante A entrena con 2 hilos y reserva 2 completos; los pares d..g de los casos difíciles quedan como probe. El constructor aborta si algún texto de train coincide (crudo o normalizado) con val, test, batería, hilos reservados o probe. Se mide además el solape de 4-gramas.
4. **Misma receta, un solo cambio.** Misma configuración, semillas y normalizador que el modelo final; solo se añaden datos con peso 3.0 (fijado de antemano, sin ajustar).
5. **Criterios de adopción fijados antes de ver resultados** (`src/evaluation/comparar_v5.py`): (a) test oficial sin regresión, (b) batería sin perder más de 2, (c) mejora en hilos reservados con IC pareado que no cruza cero.
6. **Modelo final** solo si se adopta: reentrenar con todos los hilos (variante F), verificando únicamente test oficial y batería.

## Límites
- Etiquetas de los hilos: una sola anotadora (Claude, guía v2.0), sin validación humana ni kappa. Son referencia razonable, no gold standard.
- "Error mínimo" no se puede garantizar: depende del techo de las etiquetas (acuerdo entre anotadores 0.81 en el corpus original) y del tamaño de los conjuntos.

## Revisión del criterio (11 de octubre de 2026)
La persona responsable aprobó la guía v2.0 como referencia para etiquetar los hilos y autorizó relajar el criterio (a): ya no se exige ΔF1 ≥ −0.010 en el test oficial, sino solo **ausencia de regresión significativa** (McNemar p ≥ 0.05). Se fijó antes de ver los resultados de la corrida de peso 1.0. La corrida de peso 3.0 (Δ −0.032, p = 0.011) falla con ambos criterios, por lo que el cambio no la rescata.

## Léxico salvadoreño y groserías afectivas (14 de octubre de 2026)
Observación de la persona responsable: en El Salvador muchas groserías no se dicen con intención de ofender (guía v2.0 §5: *cerote*, *maje*, *vergón*, *puta*, *verga* como marcadores afectivos; decide la intención y el destinatario).
- **Auditoría de los hilos etiquetados:** de 167 textos con grosería, solo 9 quedaron No Tóxico por consenso. Los hilos son hostiles y casi no tienen uso afectivo, así que **entrenar solo con ellos puede enseñar «grosería ⇒ ofensivo»**.
- **Prueba específica** (`data/evaluation/hard_cases/probe_vulgaridad_afectiva_SOLO_EVALUAR.csv`, 20 frases afectivas + 18 insultos con las mismas palabras; nunca se entrena con ella): `final5` 18/20 afectivas bien y 18/18 insultos; `final_v5` **19/20** y 18/18. El único fallo de v5: «Hijo de puta, qué suerte la tuya, felicidades por el trabajo nuevo».
- **Criterio (d) para adoptar v6, fijado antes de ver sus resultados:** las frases afectivas clasificadas como No Tóxico no bajan más de 2 respecto de v5 (≥ 17/20) y los insultos siguen detectándose (≥ 16/18).
- **Límites:** la prueba es pequeña y la escribí yo; varios hilos son de otros países (Venezuela, Chile, España), donde las mismas palabras no son afectivas igual que en El Salvador. Los datos originales de la Etapa II (Facebook/X salvadoreño) sí contienen vulgaridad afectiva etiquetada No Tóxico, y siguen en el entrenamiento.

## Política de evaluación revisada (15 de octubre de 2026)
Observación de la persona responsable: al ampliar el test con datos reales, la batería de 144 casos que escribimos queda en parte **deprecada**.
Motivos medidos: es pequeña (144), de varianza alta (una semilla varía hasta 8 aciertos; quitar 1 de 5 semillas mueve el ensamble 3 puntos), sintética y escrita por nosotros; ya bloqueó una decisión por 3 aciertos (p = 0.375) y 20 de sus textos coincidieron con filas de entrenamiento de la Etapa II.
Cambios desde ahora (no se aplican con efecto retroactivo: las decisiones ya tomadas, incluida la promoción de v3.3.0, no se reabren):
- **Criterio principal de comparación:** el **banco externo real** (`src/evaluation/banco_externo.py`: migrantes + externo 2 + militares_pandilleros, consenso de 3 anotadores, ninguna versión lo vio al entrenar) con IC y McNemar pareados.
- **Criterios de seguridad que se mantienen como umbral:** test oficial sin regresión significativa; vulgaridad afectiva salvadoreña (≥ 17/20 y ≥ 16/18); atajos por invariancia (6 familias de plantilla + `prueba_atajos_reales.py`).
- **La batería de 144 pasa a diagnóstico:** se sigue informando por grupo (útil para ver emoji y ofuscación), pero no es criterio de adopción.
- **Pendiente:** ampliar el banco con más Odio (hoy 33 + 2 + 1 casos) y validar una muestra con una persona.
