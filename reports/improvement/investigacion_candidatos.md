# Ronda 3: investigación de candidatos (29 de octubre de 2026)

Fase 0 del encargo de recolección de la ronda 3 (`docs/improvement/Plan_ronda3_amenazas_jerga.md`). Navegador: BrowserOS neo, publicaciones públicas de X.

## Método
- **Ids prohibidos:** los 11 ids de `data/annotation/threads/REGISTRO.md`. Los hilos de la fase 1 y del banco congelado (`data/evaluation/frozen_bank/`) no tienen id registrado, solo nombre, así que se evitaron sus temas (p. ej. `pandilleros_traslado`, `violadores_pena_muerte`, `presos_90mil`, `selecta`, `militares_pandilleros`). Además, `verificar_duplicados.py` compara cada hilo contra todos los CSV del proyecto, así que un hilo repetido saldría como duplicado masivo. No pasó con ninguno.
- **Búsqueda:** búsqueda «Top» de X con `min_replies:N lang:es` y los términos del encargo, más variantes (p. ej. `from:nayibbukele feliz`, `from:AlcaldeNetito`, `from:ClaudiaOrtizSV`, quejas por servicios públicos).
- **Muestra:** por cada candidato se recorrió el hilo completo (lo que X deja cargar, hasta 480 respuestas) para medir las **respuestas útiles reales** (español, ≥ 4 palabras, sin duplicados). Después se leyeron a mano las **primeras 20 a 30 útiles**: 30 en los primeros candidatos y entre 20 y 25 en los últimos (la muestra quedó por debajo de 30 en varios). Los porcentajes son estimaciones a ojo. La columna «jerga» viene de esa muestra; la cuenta automática por palabras clave sale en el informe final.
- **Descarte** (criterio sin cambios): < 120 útiles, mayoría no en español o un solo sub-tema. También se descartó un candidato por involucrar a un menor (regla del encargo) y los que no encajaban con su subgrupo (p. ej. un hilo «B» que en realidad eran ataques políticos).

## Tabla de candidatos
Muestra = recuento en la muestra leída: jerga salvadoreña / celebra o desea daño / crítica sin insulto.

| candidato (id) | tema | sub | resp. visibles | brutos | útiles | muestra (jerga / daño / crítica) | decisión | motivo |
|---|---|---|---|---|---|---|---|---|
| 1630172141478985730 | DW: el CECOT entra en funcionamiento (2023) | A1 | 350 | 232 | 214 | 1 / 8 / 4 | **elegido** | celebración del encierro, ataques a ONG y medios, alguna crítica |
| 1800695955530060129 | Menoni: traslado de 2,000 pandilleros (2024) | A1 | 393 | 206 | 152 | 1 / 10 / 2 | **reserva 1** | pasa; mayoría mexicanos |
| 1145441481236369408 | Bukele: enfrentamiento en Guatajiagua (2019) | A2 | 680 | 342 | 313 | 2 / 3 / 6 | **elegido** | único A2 que pasó; poca celebración, mucho tema de armas del FMLN |
| 1512555307154776066 | PNC: terrorista muere en Nejapa (2022) | A2 | 185 | 118 | 91 | — | descartado | < 120 útiles |
| 1852021365529829675 | Ladrón desnudo atado a un poste, Bogotá (2024) | A3 | 762 | 301 | 232 | 0 / 15 / 3 | **elegido** | apología del castigo físico («paloterapia», «ni una caricia»); región: Colombia |
| 1507866820014919687 | Dip. Gallegos: pena de muerte (2022) | A4 | 1188 | 327 | 294 | 4 / 10 / 5 | **elegido** | pena de muerte, críticas al diputado, argumentos religiosos |
| 1924346322565394519 | LPG: detienen a Ruth López, de Cristosal (2025) | A5 | 419 | 292 | 248 | 3 / 10 / 5 | **elegido** | deseos de cárcel y daño a una defensora; ambos lados |
| 2105407703858233741 | La Selecta: «Todos a apoyar» y precios de entradas (2026) | B1 | 242 | 215 | 174 | 8 / 0 / 8 | **elegido** | burla y enojo de la afición con jerga (cerote, choto, troncos) |
| 1716977184743510158 | SivarNews: pupusas a $4.55 (2023) | B2 | 833 | 337 | 306 | 5 / 0 / 6 | **elegido** | conversación casual sobre precios y pupuserías |
| 1962279517377949825 | J. Martínez d'Aubuisson: las pupusas son mesoamericanas (2025) | B2 | 709 | 329 | 303 | 10 / 3 / 4 | no elegido | mucha jerga, pero la mayoría son ataques personales al autor |
| 1255637673466671104 | ¿Pupusas de arroz o de maíz? (2020) | B2 | 171 | 100 | — | — | descartado | < 120 útiles |
| 1698800483043787164 | AlcaldeNetito: el diputado «Alfredo Adame» mete las patas (2023) | B3 | 195 | 153 | 148 | 4 / 0 / 3 | **elegido** | burla política ligera; respuestas casuales con jerga (nambe, chele, bro) |
| 1771771361314189488 | AlcaldeNetito: baile en Santa Ana (2024) | B3 | 242 | 168 | 155 | 2 / 1 / 3 | descartado | el tema involucra a un menor |
| 1803272533937954997 | AlcaldeNetito: «No lo quiero… LO NECESITO» (2024) | B3 | 191 | 127 | 56 | — | descartado | < 120 útiles (respuestas de solo emoji o imagen) |
| 1742351822147486061 | J. Freixas: «Voy a comer pupusas con Messi» (2024) | B3 | 208 | 136 | 93 | — | descartado | < 120 útiles |
| 1948081935248425243 | W. Araujo: ¿qué personaje cae mal? (2025) | B3 | 513 | 294 | 222 | 5 / 1 / 2 | descartado | no es humor: encuesta política con insultos |
| 2096959215759667578 | CroniGuanacas: tráfico, ¿restricción por placas? (2026) | B4 | 235 | 205 | 196 | 4 / 0 / 8 | **elegido** | debate casual sobre tráfico y buses |
| 1600323628066742272 | Bukele: «Feliz aniversario mi amor» (2022) | B5 | 2466 | 312 | 259 | 0 / 0 / 1 | **elegido** | felicitaciones; casi sin jerga |
| 1438164354336178176 | Bukele: «Feliz cumpleaños El Salvador», bicentenario (2021) | B5 | 712 | 286 | 236 | 3 / 0 / 6 | no elegido | mezcla celebración y protesta (#el15marchamos) |
| 1355902896043266050 | ¿14 o 28 de febrero? (2021) | B5 | 164 | 96 | — | — | descartado | < 120 útiles; además es electoral |
| 1867041570341478431 | Rodro77: ¿qué afición es más grande? (2024) | B6 | 219 | 178 | 153 | 6 / 0 / 2 | **elegido** | bromas e insultos cariñosos entre aficionados de Alianza, Águila y FAS |
| 1916602834121888249 | Bukele: la canasta básica bajó (2025) | C1 | 1088 | 330 | 228 | 1 / 0 / 7 | **elegido** | crítica al gobierno ~32 %, a favor ~60 % |
| 1542217373612183552 | Queja por la atención en el Hospital Rosales (2022) | C1 | 193 | 138 | 131 | 1 / 0 / 12 | **reserva 2** | crítica de gestión sin insulto ~50 %; menos de 225 útiles |
| 1951655790835568651 | DW: críticas a la reelección indefinida (2025) | C1 | 446 | 311 | 291 | 1 / 0 / 4 | descartado | casi todo defiende al gobierno (crítica ~8 %) |
| 1951240388846481769 | F. Loaiza: reelección indefinida (2025) | C1 | 400 | 288 | 257 | 0 / 0 / 4 | descartado | respuestas desde España; ~75 % defiende a Bukele con insultos |
| 2114787718656131557 | H. Silva Ávalos: gobierno «cobarde» ante la CIDH (2026) | C1 | 304 | 252 | 200 | 7 / 1 / 2 | descartado | casi todo son insultos al autor |
| 1682362905591701504 | P. Marrohs: despiden a 12 médicos del Rosales (2023) | C1 | 792 | 327 | 305 | 1 / 2 / 3 | descartado | ~80 % apoya al gobierno |
| 1855967978732347895 | Raudales: «pérdidas no realizadas» de bitcoin (2024) | C1 | 196 | 155 | 140 | 6 / 1 / 2 | descartado | insultos al autor, casi sin crítica al gobierno |
| 1932964897849246176 | C. Ortiz: propuesta para migrantes retornados (2025) | C2 | 289 | 210 | 189 | 3 / 1 / 10 | **elegido** | crítica sin insulto a una diputada opositora ~43 % |
| 1275956957577449472 | K. Osorio: ARENA y la feria en pandemia (2020) | C2 | 524 | 325 | 300 | 3 / 1 / 8 | no elegido | pasa, pero tiene más insultos que el elegido |
| 1301157066199924736 | ARENA: 82,000 empleos perdidos (2020) | C2 | 199 | 147 | 138 | 1 / 0 / 9 | no elegido | pasa; respuestas critican sobre todo a ARENA y FMLN |
| 1396906833311322116 | E. Muyshondt: alza de la canasta básica (2021) | C2 | 621 | 329 | 294 | 5 / 1 / 8 | no elegido | pasa; crítica al exalcalde de ARENA, muchos insultos |
| 1603219880773296128 | C. Ortiz: préstamo del viaducto Los Chorros (2022) | C2 | 656 | 306 | 283 | 6 / 0 / 3 | no elegido | ataques a la diputada, mayoría con insultos |

| 1712997998534209549 | ITR: la Selecta cae ante Martinica y desciende (2023) | B1 | 238 | 194 | 179 | 3 / 0 / 8 | **adicional** | frustración de la afición con jerga (uta, riata); muestra de 25 |
| 1802855302129123500 | SivarNews: empleados de pupusería tiran basura en tragantes (2024) | B4 | 219 | 177 | 156 | 1 / 2 / 10 | **adicional** | vida cotidiana; piden multas y castigos, algunos insultos; muestra de 30 |

## Selección
13 hilos que pasan: A1, A2, A3, A4, A5 · B1, B2, B3, B4, B5, B6 · C1, C2 (marcados **elegido**).
Reservas: **Menoni, traslado 2024** (A1) y **Hospital Rosales** (C1).
Después se añadieron 2 hilos B (**adicional**) para llegar a ~3,000 textos y cubrir el déficit de B. Las reservas siguen sin usarse.

## Observaciones
- **Equilibrio de lados en C.** Por hilo, C1 y C2 quedan en 55 % y 45 % de los textos de C. Por contenido no: en X, las respuestas sobre política salvadoreña son mayoritariamente oficialistas. De 8 candidatos C1 revisados, solo el del Hospital Rosales llega a ~50 % de crítica al gobierno (y tiene 131 útiles). En el C1 elegido (canasta básica) la crítica al gobierno ronda el 32 %. Las búsquedas de quejas por servicios (ANDA, ISSS, apagones, recibos, pasaje) no devolvieron hilos con ≥ 120 respuestas.
- **A2** tuvo un solo candidato que pasa y su porcentaje de celebración es bajo (~10 %).
- **B3 y B5** son los subgrupos más flojos para el objetivo de jerga. B3 es burla política ligera, no memes, y B5 son felicitaciones formales casi sin jerga.
