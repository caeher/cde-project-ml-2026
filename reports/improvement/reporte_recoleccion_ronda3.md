# Ronda 3: informe de recolección (29 de octubre de 2026)

Recolección con BrowserOS neo sobre respuestas públicas de X. Solo se leyó y se guardó texto: no hubo respuestas, likes, reposts ni follows, y no se etiquetó nada.
Candidatos y criterios: `reports/improvement/investigacion_candidatos.md`.

## Hilos recolectados
Brutos = respuestas que recogió el colector (sin la publicación original). Limpieza = español, ≥ 4 palabras, sin menciones, URL ni anuncios, sin repetidos dentro del hilo. Final = tras quitar duplicados del proyecto y los textos retirados por privacidad.

| hilo | id de la publicación | grupo | sub | brutos | tras limpieza | duplicados quitados | privacidad | final | archivo |
|---|---|---|---|---|---|---|---|---|---|
| cecot_inauguracion | 1630172141478985730 | A | A1 | 232 | 214 | 2 | 0 | **212** | `A1_cecot_inauguracion.csv` |
| enfrentamiento_guatajiagua | 1145441481236369408 | A | A2 | 342 | 313 | 2 | 0 | **311** | `A2_enfrentamiento_guatajiagua.csv` |
| ladron_poste_bogota | 1852021365529829675 | A | A3 | 301 | 232 | 1 | 0 | **231** | `A3_ladron_poste_bogota.csv` |
| pena_muerte_gallegos | 1507866820014919687 | A | A4 | 327 | 294 | 0 | 3 | **291** | `A4_pena_muerte_gallegos.csv` |
| captura_ruth_lopez | 1924346322565394519 | A | A5 | 292 | 248 | 0 | 0 | **248** | `A5_captura_ruth_lopez.csv` |
| selecta_entradas | 2105407703858233741 | B | B1 | 215 | 172 | 0 | 0 | **172** | `B1_selecta_entradas.csv` |
| pupusas_precio | 1716977184743510158 | B | B2 | 337 | 306 | 0 | 0 | **306** | `B2_pupusas_precio.csv` |
| diputado_adame | 1698800483043787164 | B | B3 | 153 | 148 | 0 | 0 | **148** | `B3_diputado_adame.csv` |
| trafico_placas | 2096959215759667578 | B | B4 | 205 | 196 | 0 | 0 | **196** | `B4_trafico_placas.csv` |
| aniversario_presidencial | 1600323628066742272 | B | B5 | 312 | 259 | 2 | 0 | **257** | `B5_aniversario_presidencial.csv` |
| aficion_alianza_fas | 1867041570341478431 | B | B6 | 178 | 153 | 0 | 0 | **153** | `B6_aficion_alianza_fas.csv` |
| canasta_basica | 1916602834121888249 | C | C1 | 330 | 228 | 0 | 1 | **227** | `C1_canasta_basica.csv` |
| propuesta_retornados | 1932964897849246176 | C | C2 | 210 | 189 | 1 | 0 | **188** | `C2_propuesta_retornados.csv` |
| selecta_martinica (adicional) | 1712997998534209549 | B | B1 | 194 | 179 | 0 | 0 | **179** | `B1_selecta_martinica.csv` |
| pupuseria_tragantes (adicional) | 1802855302129123500 | B | B4 | 177 | 156 | 0 | 0 | **156** | `B4_pupuseria_tragantes.csv` |
| **total** | | | | **3,805** | **3,287** | **8** | **4** | **3,275** | |

Archivos en `data/sources/x_threads/phase3/`: CSV UTF-8 con BOM, columnas `ID,hilo,grupo,subgrupo,texto`, IDs `P3-00001`…`P3-03718`. Hay huecos en la numeración (ver «Incidencias»).
Los 15 ids están registrados en `data/annotation/threads/REGISTRO.md` (sección «Ronda 3»).
Los dos hilos **adicionales** se recolectaron después de la selección inicial para llegar a ~3,000 textos y cubrir el déficit de B. Son 15 hilos en total en lugar de 13: B1 y B4 tienen dos hilos cada uno.

## Totales frente a objetivo
| grupo | textos | objetivo | estado |
|---|---|---|---|
| A: celebración, apología o deseo de daño | 1,293 | ≥ 1,000 | cumple |
| B: conversación casual con jerga | 1,567 | ≥ 1,250 | cumple (tras los 2 hilos adicionales) |
| C: crítica política sin insultos | 415 | ≥ 400 | cumple |
| **Total** | **3,275** | ~3,000 (mínimo 2,500) | cumple |

**Jerga (estimación automática, no es etiqueta):** 161 textos contienen alguna palabra de una lista de jerga salvadoreña (B 100, A 39, C 22). Es una cota inferior, porque la lista no cubre toda la jerga. Con esa cifra, el objetivo de ≥ 300 No Tóxico con jerga y ≥ 100 Ofensivo con jerga **probablemente no se alcanza**. Se confirmará cuando los anotadores etiqueten.

**Equilibrio de lados en C:** por hilo, C1 tiene 227 textos (55 %) y C2 188 (45 %). Por contenido, el lado crítico al gobierno se estima en ~30 % del grupo C. La crítica al gobierno es minoritaria incluso en el hilo C1 (~32 % en la muestra), así que el criterio de 40 % **no se cumple por contenido**. Se revisaron 8 candidatos C1 y solo uno (Hospital Rosales, reserva 2) llegaba a ~50 %, pero tiene 131 útiles.

## Verificación de duplicados
`src/data/threads/verificar_duplicados.py` (exacto, normalizado y casi ≥ 0.8, contra todos los CSV de `data/` y `archivo/`), ejecutado tras cada hilo:
- A1: 2 exactos (con `externo_militares.csv` del archivo y con `blind/lote_P2.csv`).
- A2: 1 exacto (con `history/v1.3.0/train.csv`) y 1 casi duplicado (con A4 de esta ronda).
- A3: 1 exacto (con `blind/lote_P4.csv`).
- C2: 1 exacto (con A3 de esta ronda).
- El resto: 0.

Se quitaron todos y se volvió a ejecutar el script hasta código 0. Tablas en `reports/improvement/dup_<hilo>.csv` (primera pasada) y `dup_<hilo>_v2.csv` (tras limpiar).
Los 2 hilos adicionales salieron con 0 duplicados.
**Pasada final** sobre los 15 archivos juntos (3,275 textos): 0 duplicados, código 0 (`dup_ronda3_final.csv`).
Una comprobación extra encontró casi duplicados que el script no marca, cuando un texto es el comienzo de otro (similitud < 0.8): 2 saludos cortos en B5, quitados, y 1 en A4, que se quitó por privacidad.

## Revisión de privacidad
- Muestra aleatoria de 40 textos (semilla 2026): ninguno identifica a un particular.
- Búsqueda por patrones (teléfonos, correos, DUI, «le dicen», «mi número»): se quitaron 4 textos. Uno trae un teléfono personal (C1), otro un correo (A4), y dos copias señalan a un supuesto ladrón por su apodo y por la calle y el taller donde se esconde (A4).
- Las menciones a figuras públicas (diputados, periodistas, defensores) se conservan: son el objeto de A5 y C.

## Incidencias
- **Cuenta de X en el perfil del navegador:** el perfil de BrowserOS ya tenía una sesión de X abierta. No inicié sesión; solo se leyó. No apareció ningún muro de login, CAPTCHA ni verificación de edad.
- **Límites del navegador:** hasta 3 pestañas por ejecución. Las esperas fueron explícitas: el colector marca la página al terminar y se espera ese selector. Varias ejecuciones superaron los 30 s del entorno; se repitieron con esperas más cortas, sin pérdida de datos porque el colector sigue en la página. Una vez se perdió el grupo de pestañas al cerrarlas todas y se recuperó abriendo una nueva. Ningún colector falló ni tuvo que reiniciarse.
- **X limita las respuestas cargadas** (entre ~100 y ~480 por hilo). Por eso 6 candidatos quedaron por debajo de 120 útiles.
- **Candidatos descartados:** 21 en total, con su motivo en `investigacion_candidatos.md`. Entre ellos, 1 por involucrar a un menor y 4 por tener < 120 útiles.
- **Ningún reemplazo** después de la selección.
- **Cambio de orden respecto al encargo:** para medir las respuestas útiles reales, cada candidato se recorrió entero durante la fase 0, y los CSV se escribieron en cuanto el hilo quedaba elegido, no al cerrar la lista de 13. Dos hilos (Hospital Rosales y ARENA/feria) se escribieron y luego salieron de la selección; se movieron fuera de `data/`, y por eso faltan los IDs P3-01976…02275 y P3-02535…02665.
- **Limpieza:** se quitaron menciones, URL y 2 anuncios (B1). Los saltos de línea se convirtieron en espacios. Emojis, ortografía, hashtags y jerga quedaron intactos. Idioma según la etiqueta de X (`es`); textos sin idioma (`und`) se aceptaron si tenían ≥ 2 palabras funcionales del español.

## Lo que no se hizo o quedó corto
- Objetivo de jerga (≥ 300 NT y ≥ 100 Ofensivo con jerga): sin verificar y probablemente no alcanzado (cota automática: 161 textos con jerga). Los hilos con más jerga encontrados eran hostiles: ataques a un periodista por las pupusas, bitcoin, Muyshondt, Silva Ávalos.
- Equilibrio de lados en C por contenido (~30 % crítico al gobierno, objetivo 40–60 %).
- Muestra de 30 por candidato: en los últimos candidatos se leyeron entre 20 y 25.
- Resúmenes cada 3 hilos: solo se dio uno intermedio (tras 7 hilos), además de este informe.
- No se etiquetó nada; eso queda para los anotadores.
