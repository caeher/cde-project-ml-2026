# Impacto social y recomendaciones de política pública (borrador)

> Borrador para la sección «Impacto social» de la Etapa II (15 pts) y el capítulo correspondiente de la tesina. Cifras del modelo v3.4.0, tomadas de `reports/fase3_candidatos.md` y `reports/fairness.md`.

## 1. Qué problema resuelve y para quién
El discurso de odio y la violencia verbal en redes sociales salvadoreñas se moderan hoy a mano, sin criterio común y casi siempre después del daño. El clasificador asigna cada publicación a una de cuatro clases (No Tóxico, Lenguaje Ofensivo, Discurso de Odio, Amenazas/Violencia) con una probabilidad calibrada. Está pensado como **apoyo a la moderación**: ordena y prioriza lo que una persona debe revisar, no decide sanciones.

Usuarios previstos: equipos de moderación de medios y organizaciones de la sociedad civil, investigadores que monitorean el discurso público y, con las salvedades de la sección 4, instituciones que quieran medir la magnitud del problema.

## 2. Beneficios esperados
- **Priorización:** las amenazas y el odio dirigido a grupos suben en la cola de revisión; el volumen de lenguaje neutro se filtra.
- **Criterio explícito y repetible:** la guía de anotación v2.0 (precedencia Amenazas > Odio > Ofensivo > No Tóxico) hace visible qué se considera cada cosa, algo que hoy depende de quien modera.
- **Lectura del contexto local:** el léxico salvadoreño tiene groserías afectivas («cerote», «maje», «vergón») que un filtro por palabras marcaría como ofensivas. El modelo se evaluó específicamente con una sonda de 20 frases afectivas y 18 insultos con las mismas palabras (resultado final: 18 de 20 afectivas bien clasificadas como No Tóxico y 17 de 18 insultos detectados).
- **Corre en local:** no envía texto de usuarios a servicios externos, lo que reduce el riesgo de privacidad frente a una API de terceros.

## 3. Riesgos y daños posibles (y qué se midió)
| Riesgo | Por qué importa | Evidencia en este proyecto |
|---|---|---|
| **Falsos positivos** sobre texto legítimo | Una sanción errónea silencia a una persona o a un grupo | Tasa de falsos positivos sobre No Tóxico: 0.112 en el banco congelado (0.146 en el test oficial); informe por grupo en `reports/fairness.md` |
| **Odio no detectado** | El daño a los grupos atacados continúa | Recall de Odio 0.67 (0.63 de media entre semillas) y de Amenazas 0.47: **cerca de un tercio del odio y más de la mitad de las amenazas no se detectan** |
| **Sesgo por jerga y dialecto** | La jerga salvadoreña podría marcarse más que el español neutro | **Confirmado:** en el test oficial el 38 % de los textos No Tóxico con jerga se marca como tóxico, frente al 7 % sin jerga (n = 29 con jerga; en v3.3.0 era 24 %). Fairness §2 |
| **Sobremarcado de menciones** | Que nombrar a un grupo (migrantes, LGBT) active la alerta aunque el texto sea neutro | El 22 % de los No Tóxico que mencionan una nacionalidad se marca tóxico (el doble de la tasa global de 11 %). Fairness §4 |
| **Etiquetas con sesgo del anotador** | Los anotadores fueron modelos de lenguaje, sin validación humana | Declarado como limitación principal; κ entre anotadores y banco por consenso de 3 |
| **Uso fuera de propósito** | Vigilancia de personas, sanción automática, uso político | Ver recomendaciones |
| **Deriva** | El lenguaje cambia (nuevos insultos, nuevas amenazas, eventos) | El modelo se entrenó con datos de 2026; requiere reevaluación periódica |

## 4. Recomendaciones de política pública y de uso
0. **Plataforma:** el rendimiento es mejor en X (F1 0.865) que en Facebook (0.761); no usar los umbrales de X para Facebook sin recalibrar.
1. **Humano en el bucle, siempre.** El modelo no debe tomar decisiones de sanción ni de denuncia sin revisión de una persona. La interfaz del prototipo muestra la probabilidad y avisa cuando la confianza es baja (< 55 %), para que esos casos vayan a revisión.
2. **Umbrales por clase y por consecuencia.** Para acciones leves (reducir alcance, poner en cola) puede bastar la predicción; para acciones graves (suspensión, denuncia) debe exigirse revisión humana y confianza alta. El umbral para Amenazas debe ser más sensible que el de Ofensivo, porque el costo de no detectar es distinto.
3. **Transparencia y apelación.** Quien reciba una moderación derivada del sistema debe saber que se usó, qué clase se le asignó y cómo apelar.
4. **Auditoría periódica de sesgo.** Repetir `fairness.py` cada vez que se reentrene o cambie el tipo de texto, y publicar los resultados con intervalos de confianza. Los grupos con pocos casos deben marcarse como «sin potencia» y no usarse para afirmar equidad.
5. **Retención mínima de datos.** El repositorio público conserva identificadores de hilo y etiquetas de consenso, no nombres de usuario. En producción, almacenar solo lo necesario para la revisión y borrarlo con un plazo definido.
6. **Participación.** Antes de un despliegue real, validar la guía y una muestra de etiquetas con personas de los grupos afectados y con moderadores locales, algo que este proyecto no pudo hacer.
7. **No usar el modelo para identificar o perseguir a personas.** Está calibrado para clasificar mensajes, no para evaluar a sus autores.
8. **Límite de uso político.** Una herramienta de este tipo puede usarse para silenciar disidencia. Se recomienda que su uso institucional sea público, con reglas escritas y supervisión independiente.

## 5. Límites que deben acompañar cualquier cifra
- Etiquetas de consenso de anotadores LLM (Sonnet, Opus y un tercer modelo), sin validación humana: los errores pueden estar correlacionados.
- Datos de X (más una parte original de Facebook en el test oficial); no se evaluó otro tipo de contenido (imágenes, audio, mensajes privados).
- Banco de evaluación pequeño en algunas clases: los intervalos de confianza de Odio son amplios.
- No se midió sesgo por autor individual ni se evaluó el impacto real en una operación de moderación.

## 6. Cómo se conecta con la rúbrica
Este documento responde a «Impacto social»: beneficios (sección 2), riesgos con evidencia medida (3), recomendaciones concretas (4) y límites (5). El análisis cuantitativo de sesgos está en `reports/fairness.md` (rúbrica: «Análisis de sesgos y ética»).
