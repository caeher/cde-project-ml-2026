# Guion del video demo (≤ 3 min)

Preparación: ejecutar `.\scripts\arrancar_demo.ps1` y abrir `http://localhost:8501` antes de grabar. Grabar la pantalla del navegador; voz en off a ritmo tranquilo (≈ 150 palabras por minuto, unas 430 en total).

| Tiempo | Pantalla | Texto |
|---|---|---|
| 0:00–0:20 | Título y panel de la app | «Este es un clasificador de toxicidad y discurso de odio para texto de redes sociales de El Salvador. Distingue cuatro clases: no tóxico, lenguaje ofensivo, discurso de odio y amenazas.» |
| 0:20–0:45 | Barra lateral con las clases | «Las clases siguen una guía de anotación propia. Si un texto cumple varias, gana la más grave: amenazas, luego odio, luego ofensivo.» |
| 0:45–1:15 | Ejemplo «saludo afectivo con grosería» | «En El Salvador muchas groserías son cariñosas. Aquí un saludo entre amigos con una palabra fuerte: el modelo lo clasifica como no tóxico, con su probabilidad.» |
| 1:15–1:45 | Ejemplo «insulto directo» y «discurso de odio» | «El mismo vocabulario dirigido contra una persona es ofensivo. Y una generalización contra un grupo, como los migrantes, es discurso de odio.» |
| 1:45–2:10 | Ejemplo «amenaza», texto con baja confianza | «Cuando el modelo duda, la app avisa y manda el caso a revisión humana. No es un veredicto: es un apoyo para quien modera.» |
| 2:10–2:40 | `reports/fairness.md` o diapositiva con cifras | «Lo medimos con un banco de 1,391 textos de hilos reales que el modelo nunca vio. F1-macro 0.72, con una mejora frente a la versión anterior. Pero somos honestos con los límites: detecta alrededor del 63 % del discurso de odio y menos de la mitad de las amenazas, y marca más texto con jerga.» |
| 2:40–3:00 | Cierre con el repositorio | «Corre en local, con un solo modelo de 418 MB, sin enviar texto a terceros. El código, la guía y el informe de sesgos están en el repositorio público.» |

Notas:
- Las cifras se toman de `reports/fase3_candidatos.md` y `reports/fairness.md`; si se reentrena, actualizarlas.
- Mostrar la advertencia de confianza baja con un texto ambiguo (probar antes cuál sale por debajo de 55 %).
