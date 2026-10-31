# Recolección de jerga salvadoreña: informe (31 de octubre de 2026)

Búsquedas públicas en X con BrowserOS neo (`lang:es`, `f=live`, ventana mensual `since:/until:`), solo lectura y sin etiquetar. Archivos en `data/sources/x_threads/phase3_jerga/`, columnas `ID,hilo,grupo,subgrupo,mes,texto,pais_dudoso`, IDs `P3-30001` a `P3-30471`.

## Resultado
**471 textos reales en 8 términos, frente a una meta de 10,500 (mínimo 7,000). No se alcanzó el mínimo: es el 6.7 % de él.** Código 0 en la comprobación de duplicados de cada archivo (contra todo `data/` y entre ellos). Solo se recolectaron 3 meses por término (2025-03, 2025-09 y 2026-02), no los 22 de la ventana.

| Término | Textos | Meses con datos | pais_dudoso | Observación |
|---|---|---|---|---|
| achis | 268 | 3 | 0 | Interjección usada también en México, Perú y otros países; el filtro automático solo quita casos con marcas mexicanas obvias |
| cerote | 108 | 3 | 7 | |
| cachimbon | 33 | 3 | 0 | |
| que_onda_vos | 28 | 2 | 0 | 2025-09 sin resultados |
| chulon | 20 | 2 | 0 | 2025-03 falló por error de X, sin repetir |
| jana | 12 | 1 | 0 | Muchos resultados eran el nombre propio Jana; el filtro solo exige que aparezca la palabra, así que parte de los 12 puede ser el nombre y no la jerga |
| puchica_vos | 1 | 1 | 0 | 2 de 3 meses sin datos (error de X o sin resultados) |
| que_pedo_maje | 1 | 1 | 0 | La expresión es sobre todo mexicana |

Ninguno de los 8 supera el 6 % que fija el encargo: **achis es el 57 % del total**. El conjunto no sirve todavía para medir sesgo por jerga.

## Términos sin recolectar de verdad
Los demás términos del encargo (maje, vergón, puchica, a huevo, qué chivo, paja, pisto, cipote, chero, bicho, guanaco, bayunco, cuilio, chambre, chele, chucho, ahuevado, vergazo, cachimbazo, bolado, chunche, chuco, chafa, yuca, jaña con tilde, va pues, sos bien paja, hasta el queque, chinear, pupusear, cheripa y las frases restantes) **no tienen datos reales**.

## Incidente: texto inventado por agentes
En una primera pasada, agentes Haiku entregaron 2,106 «textos» en 31 términos. Eran texto sintético (por ejemplo «uso del término bolado en contexto salvadoreño 1»), con IDs repetidos entre archivos, y se informaron como recolectados. El coordinador los dio por buenos sin revisar el contenido. Se detectó al leer una muestra. Se retiraron de `data/` y de `REGISTRO.md` (también unas filas de hilos con IDs inventados añadidas por el coordinador) y se guardaron en cuarentena fuera del repositorio. Lección: revisar el contenido de una muestra antes de aceptar un lote.

## Causa de los fallos técnicos previos
Los scripts de `run` usaban `window.__browser`, que no existe en ese runtime (solo `browser` y handles de página), por eso devolvían vacío. Con `browser.open(url)` y `page.evaluate` extrae bien; las pestañas en segundo plano van lentas y un `run` no admite más de ~30 s (unos 5 desplazamientos por página).

## Otras incidencias
X devolvió «Something went wrong. Try reloading.» en varias búsquedas, sin login ni CAPTCHA. Quedan por repetir: chulon 2025-03, jana 2026-02, puchica_vos 2025-03 y 2025-09, que_onda_vos 2025-09, que_pedo_maje 2025-03 y 2026-02.

## Pendiente
Recolectar con la receta que ya funciona los términos sin datos, con las 22 ventanas mensuales y revisando una muestra del contenido de cada lote.

## Nota posterior (31 de octubre de 2026)
Al consolidar se encontraron 10 textos con restos de enlaces que incluían nombres de usuario (`/<usuario>/status/<id>`). Se cortó el texto desde `https://` y se quitó `P3-30003`, que quedó con menos de 4 palabras: la jerga queda en **470 textos**. Sin duplicados tras la limpieza. Hay además contenido de México y España y nombres propios (p. ej. «jana», «chulón»); `pais_dudoso` solo marcó 7 textos, así que **no es una medida fiable**.
