# Registro de hilos de X recolectados (octubre 2026)

Recolección con BrowserOS neo (navegador de agentes), 10–14 de octubre de 2026, sobre publicaciones públicas.
Se guarda solo el texto de las respuestas (sin usuario, menciones ni URL). Identificador = id de la publicación original en X.

| Hilo | Tema | Id de publicación | Respuestas útiles | Uso |
|---|---|---|---|---|
| estadio (prueba inicial) | Estadio Nacional | 2108273363332599809 | 199 | solo exploración, sin etiquetas |
| repatriados | Venezolanos repatriados del CECOT | 1946639925274669495 | 119 etiquetadas | entrenamiento |
| canje | Canje humanitario de presos | 1914139086316572974 | 170 etiquetadas | entrenamiento |
| invasion | «Invasión» a El Salvador | 1910028961305788722 | 180 etiquetadas | entrenamiento |
| feminismo | Feministas y recuento de votos | 1754689811774939572 | 247 etiquetadas | entrenamiento |
| cecot | Youtuber visita el CECOT | 2004303452059623538 | 209 etiquetadas | test externo de v5; entrenamiento en v6 |
| miss_el_salvador | Miss El Salvador y bitcoin | 1613576512950657024 | 230 etiquetadas | entrenamiento en v6 |
| migrantes | Regularizar inmigrantes (Chile) | 2102203205044326541 | 308 | **test externo de v6 (nunca entrena)** |
| trans | Mujer trans vicealcaldesa | 2109855274836070665 | 143 | etiquetas por agentes ciegos |
| racismo | Racismo hacia indígenas | 2108290984362602873 | 163 | etiquetas por agentes ciegos |
| venezolanos2 | Venezolanos | 2107975293491171762 | 230 | etiquetas por agentes ciegos |

## Estructura de `data/annotation/threads/`
- `crudo/`: textos limpios por hilo, sin etiquetar (`hilos_1_a_5_limpios_todos.csv`, `migrantes_sin_etiquetar.csv`, `hilos_nuevos_sin_etiquetar.csv`).
- `hilos_etiquetados.csv`, `hilos_etiquetados_2.csv`, `test_externo_cecot.csv`: etiquetas de Claude (guía v2.0).
- `etiquetas/`: consolidado de esas 1,155 etiquetas y los diccionarios `lab*.py` con que se asignaron.
- `ciego/`: lotes sin etiquetas (`lote_*.csv`) y las salidas de los agentes anotadores independientes (`salida_*.csv`: ID, label, seguro).
- `predicciones/`: predicciones de los modelos sobre cada hilo.
- `muestra_validacion_*`: 80 textos para validación humana.

## Procedimiento de etiquetado
1. Claude etiquetó 5 hilos (1,155 textos) aplicando la guía v2.0.
2. Agentes independientes, sin ver esas etiquetas, etiquetaron los mismos textos (κ = 0.77; κ = 0.96 si el agente estaba seguro).
3. Un tercer agente desempató los desacuerdos. Los hilos nuevos (migrantes, trans, racismo, venezolanos2) los etiquetan dos agentes ciegos y un tercero desempata.
4. Solo se entrena con textos donde la mayoría de anotadores coincide.

## Fase 0 del plan de mejora (16 de octubre de 2026): banco congelado y pool de entrenamiento
Constructor único: `src/data/build_dataset_final.py` (`--selftest` comprueba que detecta fugas). Sustituye a los `build_dataset_v5…v8.py`, archivados en `archivo/scripts_build/`. Se quita la publicación original de cada hilo y los textos sin consenso.

**Banco congelado** (`data/evaluation/frozen_bank/`, SHA-256 en `MANIFEST.json`; nunca entra a entrenamiento ni a selección): `migrantes` (306), `externo2` (647), `militares_pandilleros` (202), `xenofobia_federico` (236) + test oficial (460).
**Pool de entrenamiento** (14 hilos): canje, cecot, feminismo, infierno_tierra, invasion, lgbt_bandera, lgbt_ultimahora, miss_el_salvador, pandilleros_traslado, racismo, racismo_orgullo, repatriados, trans, venezolanos2 → 2,698 filas (NT 1,493 · OF 673 · **OD 334 · AM 198**), con etiquetas blandas `p0..p3`. `data/dataset/train.csv` = 9,181 filas.
**Cuotas de la fase 1:** ≥ 700 Odio y ≥ 450 Amenazas con consenso (hoy 334 y 198).

## Fase 1 del plan de mejora — cerrada (17 de octubre de 2026)
Dos rondas de recolección dirigida con BrowserOS (18 hilos, 3,502 textos útiles tras quitar la publicación original y duplicados) y etiquetado por consenso: dos anotadores de **modelos distintos** (Sonnet y Opus) a ciegas + desempate con un tercer modelo.
- Ronda 1 (12 hilos, 2,115 textos): κ Sonnet–Opus = 0.771, 85.7 % de acuerdo, 302 desempates, 26 sin consenso.
- Ronda 2 (6 hilos de Odio, 1,387 textos): κ = 0.792, 86.7 % de acuerdo, 184 desempates, 16 sin consenso.
- Pool final: 32 hilos, 6,158 filas → **Odio 850 (cuota 700 ✓) · Amenazas 559 (cuota 450 ✓)**; `data/dataset/train.csv` = 12,641 filas.
- Limitación declarada: todos los anotadores son LLM (errores correlacionados); Opus es más estricto con insultos leves que Sonnet (534 vs 401 Ofensivo en la ronda 1). Un incidente de archivos temporales compartidos en la ronda 1 se corrigió exigiendo directorios propios.

## Ronda 3 del plan de mejora: amenazas y jerga (29 de octubre de 2026)
Plan en `docs/improvement/Plan_ronda3_amenazas_jerga.md`. Recolección con BrowserOS neo; 15 hilos, 3,275 textos **sin etiquetar** en `data/sources/x_threads/phase3/` (IDs `P3-…`). Detalle en `reports/improvement/reporte_recoleccion_ronda3.md` y candidatos en `reports/improvement/investigacion_candidatos.md`.

| Hilo | Tema | Id de publicación | Respuestas útiles | Uso |
|---|---|---|---|---|
| cecot_inauguracion | El CECOT entra en funcionamiento (A1) | 1630172141478985730 | 212 | sin etiquetar |
| enfrentamiento_guatajiagua | Enfrentamiento en Guatajiagua (A2) | 1145441481236369408 | 311 | sin etiquetar |
| ladron_poste_bogota | Ladrón atado a un poste, Bogotá (A3) | 1852021365529829675 | 231 | sin etiquetar |
| pena_muerte_gallegos | Pena de muerte, dip. Gallegos (A4) | 1507866820014919687 | 291 | sin etiquetar |
| captura_ruth_lopez | Detención de Ruth López (A5) | 1924346322565394519 | 248 | sin etiquetar |
| selecta_entradas | La Selecta y precio de entradas (B1) | 2105407703858233741 | 172 | sin etiquetar |
| selecta_martinica | La Selecta cae ante Martinica (B1) | 1712997998534209549 | 179 | sin etiquetar |
| pupusas_precio | Pupusas a $4.55 (B2) | 1716977184743510158 | 306 | sin etiquetar |
| diputado_adame | Burla al diputado «Alfredo Adame» (B3) | 1698800483043787164 | 148 | sin etiquetar |
| trafico_placas | Tráfico y restricción por placas (B4) | 2096959215759667578 | 196 | sin etiquetar |
| pupuseria_tragantes | Pupusería tira basura en tragantes (B4) | 1802855302129123500 | 156 | sin etiquetar |
| aniversario_presidencial | «Feliz aniversario mi amor» (B5) | 1600323628066742272 | 257 | sin etiquetar |
| aficion_alianza_fas | ¿Qué afición es más grande? (B6) | 1867041570341478431 | 153 | sin etiquetar |
| canasta_basica | La canasta básica bajó (C1) | 1916602834121888249 | 227 | sin etiquetar |
| propuesta_retornados | Propuesta para migrantes retornados (C2) | 1932964897849246176 | 188 | sin etiquetar |

Las reservas (Menoni 1800695955530060129, Hospital Rosales 1542217373612183552) y los demás candidatos revisados no se usaron y no están en `data/`.

## Ampliación de la ronda 3 hasta 25 mil (29 de octubre de 2026)
Detalle en `reports/improvement/reporte_recoleccion_ampliacion_25mil.md`. Mismo método: BrowserOS neo, solo lectura, sin etiquetar. Los hilos de abajo no se pueden reutilizar.

| Archivo (`data/sources/x_threads/phase3/`) | Tema | Id de publicación | Textos finales | Uso |
|---|---|---|---|---|
| A10_tercer_aniversario_regimen.csv | tercer aniversario regimen (A10) | 1905449849614459355 | 239 | sin etiquetar |
| A11_casi_600_capturas.csv | casi 600 capturas (A11) | 1508270604872523779 | 280 | sin etiquetar |
| A12_emma_dejar_morir_hambre.csv | emma dejar morir hambre (A12) | 1689712820584148992 | 271 | sin etiquetar |
| A13_megacarcel_12000.csv | megacarcel 12000 (A13) | 1716152583650234520 | 290 | sin etiquetar |
| A14_movilizacion_70.csv | movilizacion 70 (A14) | 1686412797222014976 | 148 | sin etiquetar |
| A15_duro_golpe_pandilleros.csv | duro golpe pandilleros (A15) | 1658848030928302080 | 223 | sin etiquetar |
| A16_cecot_pandilleros_esto_es.csv | cecot pandilleros esto es (A16) | 1945269189549113453 | 207 | sin etiquetar |
| A17_solicito_regimen_asamblea.csv | solicito regimen asamblea (A17) | 1507901269138194433 | 256 | sin etiquetar |
| A18_cena_navidad_cecot.csv | cena navidad cecot (A18) | 1740780091993374915 | 305 | sin etiquetar |
| A19_convoca_consejo_ministros.csv | convoca consejo ministros (A19) | 1518083575467368449 | 274 | sin etiquetar |
| A1_capturas_4_dias.csv | capturas 4 dias (A1) | 1509018006432665600 | 258 | sin etiquetar |
| A1_mensaje_criminales.csv | mensaje criminales (A1) | 1511160179135586308 | 245 | sin etiquetar |
| A20_brutal_venganza.csv | brutal venganza (A20) | 1766960948806385805 | 136 | sin etiquetar |
| A21_te_gustaria_delincuentes.csv | te gustaria delincuentes (A21) | 1654532026576388097 | 190 | sin etiquetar |
| A22_mega_carcel_40000.csv | mega carcel 40000 (A22) | 1620753971831836672 | 217 | sin etiquetar |
| A23_ropa_interior.csv | ropa interior (A23) | 1255390132078882816 | 317 | sin etiquetar |
| A24_mano_dura.csv | mano dura (A24) | 1636112372531118080 | 249 | sin etiquetar |
| A25_duro_golpe_criminales.csv | duro golpe criminales (A25) | 1666658433230155779 | 210 | sin etiquetar |
| A26_ocho_reclusos.csv | ocho reclusos (A26) | 1630192992815394818 | 274 | sin etiquetar |
| A27_candidato_arena_carcel.csv | candidato arena carcel (A27) | 1680727722539065344 | 304 | sin etiquetar |
| A28_criminales_carcel.csv | criminales carcel (A28) | 1570167309691662338 | 142 | sin etiquetar |
| A29_sobreviviente_terror.csv | sobreviviente terror (A29) | 1658506334512328705 | 235 | sin etiquetar |
| A30_segundo_grupo_traslado.csv | segundo grupo traslado (A30) | 1636074901684494337 | 282 | sin etiquetar |
| A31_cecot_familia.csv | cecot familia (A31) | 2000960861410603172 | 274 | sin etiquetar |
| A32_pandilleros_cecot_piensan.csv | pandilleros cecot piensan (A32) | 1639527660983336962 | 160 | sin etiquetar |
| A33_madrugada_ejecuta.csv | madrugada ejecuta (A33) | 1629249512337293315 | 214 | sin etiquetar |
| A34_regimen_se_rien.csv | regimen se rien (A34) | 1698010558048370871 | 154 | sin etiquetar |
| A35_confinamiento_terrorismo.csv | confinamiento terrorismo (A35) | 1620752336556523522 | 207 | sin etiquetar |
| A36_mega_carcel_mensaje.csv | mega carcel mensaje (A36) | 1620863483553394689 | 252 | sin etiquetar |
| A5_familiares_detenidos.csv | familiares detenidos (A5) | 1625166717449121792 | 308 | sin etiquetar |
| A6_criminalidad_bukele.csv | criminalidad bukele (A6) | 1615892766730469376 | 211 | sin etiquetar |
| A7_un_anio_regimen.csv | un anio regimen (A7) | 1640469676458164226 | 254 | sin etiquetar |
| A8_agente_asesinado.csv | agente asesinado (A8) | 1658844243677310977 | 256 | sin etiquetar |
| A9_capturas_8000.csv | capturas 8000 (A9) | 1512325092059095040 | 270 | sin etiquetar |
| B10_pupusas_mesoamericanas.csv | pupusas mesoamericanas (B10) | 1962279517377949825 | 309 | sin etiquetar |
| B11_chivo_wallet.csv | chivo wallet (B11) | 1757175168076480959 | 122 | sin etiquetar |
| B12_bitcoin_perdidas.csv | bitcoin perdidas (B12) | 1855967978732347895 | 140 | sin etiquetar |
| B13_derrota_guatemala.csv | derrota guatemala (B13) | 2104788141144264815 | 273 | sin etiquetar |
| B14_partido_puerto_rico.csv | partido puerto rico (B14) | 1798937686641967201 | 265 | sin etiquetar |
| B15_ricky_messi.csv | ricky messi (B15) | 1748411414807454154 | 216 | sin etiquetar |
| B16_aficionado_lagrimas.csv | aficionado lagrimas (B16) | 1965284913600487585 | 154 | sin etiquetar |
| B17_dt_no_es_fracaso.csv | dt no es fracaso (B17) | 1978324743645204642 | 234 | sin etiquetar |
| B18_aficionados_fito.csv | aficionados fito (B18) | 1669374081370562560 | 135 | sin etiquetar |
| B19_kurupi_millonario.csv | kurupi millonario (B19) | 2043038053246140803 | 141 | sin etiquetar |
| B20_proponen_fito.csv | proponen fito (B20) | 1701643948962238699 | 204 | sin etiquetar |
| B22_necesita_aficion.csv | necesita aficion (B22) | 1937740141230956889 | 142 | sin etiquetar |
| B23_bienvenido_bolillo.csv | bienvenido bolillo (B23) | 1894184256450220538 | 153 | sin etiquetar |
| B26_encuesta_selecta_vergonzoso.csv | encuesta selecta vergonzoso (B26) | 2104770480825913735 | 191 | sin etiquetar |
| B27_selecta_hasta_aca.csv | selecta hasta aca (B27) | 1419106929289408515 | 297 | sin etiquetar |
| B28_selecta_san_vicente.csv | selecta san vicente (B28) | 1845644179054985687 | 194 | sin etiquetar |
| B29_tenemos_selecta.csv | tenemos selecta (B29) | 1419107392504086532 | 259 | sin etiquetar |
| B31_jairo_empate.csv | jairo empate (B31) | 1798942561887015037 | 167 | sin etiquetar |
| B32_rubén_botada.csv | rubén botada (B32) | 1736907286847648094 | 132 | sin etiquetar |
| B33_alcalde_pupuseria.csv | alcalde pupuseria (B33) | 1320716478186987521 | 282 | sin etiquetar |
| B34_albos_emplumados.csv | albos emplumados (B34) | 1824132038162543078 | 129 | sin etiquetar |
| B35_zavaleta_roldan.csv | zavaleta roldan (B35) | 1716969400195043470 | 276 | sin etiquetar |
| B36_concierto_cuscatlan.csv | concierto cuscatlan (B36) | 1964478689678414199 | 302 | sin etiquetar |
| B37_experimentados_selecta.csv | experimentados selecta (B37) | 1706363459166691592 | 123 | sin etiquetar |
| B7_intolerancia_calle.csv | intolerancia calle (B7) | 1586820581668052992 | 292 | sin etiquetar |
| B8_yeik_creador.csv | yeik creador (B8) | 2023228871374467408 | 329 | sin etiquetar |
| B9_censo_hinchas.csv | censo hinchas (B9) | 2028597746500792404 | 122 | sin etiquetar |
| C10_pasaje_un_dolar.csv | pasaje un dolar (C10) | 1980345257607754160 | 255 | sin etiquetar |
| C11_estadio_china.csv | estadio china (C11) | 1202580805505224705 | 302 | sin etiquetar |
| C12_bukele_fe.csv | bukele fe (C12) | 2114341207258316912 | 216 | sin etiquetar |
| C13_mesas_suspendidas.csv | mesas suspendidas (C13) | 1239993268160643078 | 298 | sin etiquetar |
| C14_uci_hospital.csv | uci hospital (C14) | 1570604027595083778 | 160 | sin etiquetar |
| C15_ningun_salvadoreno_haiti.csv | ningun salvadoreno haiti (C15) | 1928126228608733693 | 256 | sin etiquetar |
| C16_elecciones_encuestas.csv | elecciones encuestas (C16) | 1753833738629181949 | 285 | sin etiquetar |
| C17_oposicion_gobierno.csv | oposicion gobierno (C17) | 1816947731044417730 | 248 | sin etiquetar |
| C18_bukele_haiti.csv | bukele haiti (C18) | 2114336027976278422 | 237 | sin etiquetar |
| C19_opositores_actos.csv | opositores actos (C19) | 1835405868998779072 | 326 | sin etiquetar |
| C20_diputadas_oposicion.csv | diputadas oposicion (C20) | 1748980898677039124 | 200 | sin etiquetar |
| C21_guerra_corruptos.csv | guerra corruptos (C21) | 1665297340180185089 | 183 | sin etiquetar |
| C22_nTN24_carcel_polemica.csv | nTN24 carcel polemica (C22) | 1630304209160601601 | 318 | sin etiquetar |
| C23_tratos_inhumanos.csv | tratos inhumanos (C23) | 1638151784731488259 | 224 | sin etiquetar |
| C24_cola_bukele.csv | cola bukele (C24) | 2114156780636827803 | 236 | sin etiquetar |
| C25_apoyar_bukele.csv | apoyar bukele (C25) | 1841526343860650049 | 308 | sin etiquetar |
| C26_no_encarcelamos_oposicion.csv | no encarcelamos oposicion (C26) | 1838674900917313938 | 240 | sin etiquetar |
| C27_mensaje_prensa.csv | mensaje prensa (C27) | 1673118417811800066 | 272 | sin etiquetar |
| C28_analista_oposicion.csv | analista oposicion (C28) | 1974187926679666773 | 279 | sin etiquetar |
| C29_reeleccion_indefinida.csv | reeleccion indefinida (C29) | 1975005620404392433 | 286 | sin etiquetar |
| C30_indefinida_zavala.csv | indefinida zavala (C30) | 1918108599114457585 | 270 | sin etiquetar |
| C31_lorena_pena_movilizacion.csv | lorena pena movilizacion (C31) | 1680943994971250690 | 127 | sin etiquetar |
| C32_jaime_bayly.csv | jaime bayly (C32) | 1754856308635746466 | 162 | sin etiquetar |
| C34_elfaro_peores_tradiciones.csv | elfaro peores tradiciones (C34) | 1754550768298868745 | 248 | sin etiquetar |
| C35_dictador_amparo.csv | dictador amparo (C35) | 2071713208659046797 | 328 | sin etiquetar |
| C36_david_qva_maduro.csv | david qva maduro (C36) | 1878184453429760387 | 326 | sin etiquetar |
| C3_oposicion_regimen_popular.csv | oposicion regimen popular (C3) | 1566960564819169281 | 265 | sin etiquetar |
| C4_oposicion_mentira.csv | oposicion mentira (C4) | 1752493262667915372 | 281 | sin etiquetar |
| C5_dejen_de_discutir.csv | dejen de discutir (C5) | 1278186070312652800 | 314 | sin etiquetar |
| C6_muchas_personas_no_entienden.csv | muchas personas no entienden (C6) | 1821761488656253080 | 283 | sin etiquetar |
| C7_mexicano_dictadura.csv | mexicano dictadura (C7) | 1877762671073759651 | 311 | sin etiquetar |
| C8_director_arriaza.csv | director arriaza (C8) | 1833033998248943641 | 266 | sin etiquetar |
| C9_navidad_gasolina.csv | navidad gasolina (C9) | 1739277427229016329 | 268 | sin etiquetar |

Hilos recolectados y **descartados** por tener menos de 120 respuestas útiles (no están en `data/`):

| Hilo | Tema | Id de publicación | Respuestas útiles | Uso |
|---|---|---|---|---|
| B21_bolillo_mejor_jugada | bolillo mejor jugada | 1990657637197705581 | 115 | descartado (<120 útiles) |
| B24_arte_shitposting | arte shitposting | 1760081889212182866 | 105 | descartado (<120 útiles) |
| B25_bronquitis_reposo | bronquitis reposo | 1537809660064980992 | 105 | descartado (<120 útiles) |
| B30_define_selecta_3_palabras | define selecta 3 palabras | 2104761914223886496 | 52 | descartado (<120 útiles) |
| B38_barra_serenata | barra serenata | 1976314782052462766 | 105 | descartado (<120 útiles) |

## Ronda 3: jerga salvadoreña, recolección parcial (31 de octubre de 2026)
Búsquedas públicas en X con BrowserOS neo, solo lectura, sin etiquetar, 3 meses por término (2025-03, 2025-09, 2026-02). Archivos en `data/sources/x_threads/phase3_jerga/` (`P3-30001`…`P3-30471`). Detalle y limitaciones en `reports/improvement/reporte_recoleccion_jerga.md`. **471 textos en 8 términos; el mínimo de 7,000 no se alcanzó.** Una primera entrega de agentes con texto sintético se retiró (ver el informe).

| Archivo | Término | Textos | Uso |
|---|---|---|---|
| busqueda_achis.csv | achis | 268 | sin etiquetar |
| busqueda_cerote.csv | cerote | 108 | sin etiquetar |
| busqueda_cachimbon.csv | cachimbon | 33 | sin etiquetar |
| busqueda_que_onda_vos.csv | «qué onda vos» | 28 | sin etiquetar |
| busqueda_chulon.csv | chulon | 20 | sin etiquetar |
| busqueda_jana.csv | jana | 12 | sin etiquetar |
| busqueda_puchica_vos.csv | «puchica vos» | 1 | sin etiquetar |
| busqueda_que_pedo_maje.csv | «qué pedo maje» | 1 | sin etiquetar |

## Ronda 3: anotación a ciegas y consolidado (31 de octubre de 2026)
Textos: 25,541 de 109 hilos (`data/sources/x_threads/phase3/`) y 470 de jerga (`phase3_jerga/`; de los 471 originales se cortaron restos de enlaces con nombres de usuario en 10 textos y se quitó `P3-30003` por quedar con menos de 4 palabras). Piloto de 1,000 textos con dos anotadores: κ = 0.82.
Anotación: agentes **Haiku 5.5** a ciegas, A con la guía v2.0 completa y B con un resumen; C desempata solo los desacuerdos. **Todos los anotadores son LLM del mismo modelo** (errores correlacionados, sin validación humana). Archivos en `data/annotation/threads/blind/ronda3/`.
La anotación se cortó por el límite de gasto: 40 de 52 lotes con A y B completos, 83 textos desempatados por C (los del piloto), 1,582 desacuerdos sin desempatar, 9 lotes sin anotar, y los 470 textos de jerga **sin anotar**.
Consolidado: `data/annotation/threads/labels/ronda3_consolidado.csv` (todos los textos y su estado) y `consenso_ronda3.csv` (solo los que ya tienen consenso: 20,506). Resumen: `reports/improvement/consolidado_ronda3.md`. Script: `src/data/threads/consolidar_ronda3.py`.
Estas etiquetas **no** entran todavía al dataset: `build_dataset_final.py` no lee `consenso_ronda3.csv`, por lo que el dataset v1.8.0 y el banco congelado no cambian.

## Ronda 3: anotación terminada y dataset v1.9.0 (1 de noviembre de 2026)
Se completó la anotación con lotes de rescate (`lote_R3A_*`: textos sin etiqueta de A; `lote_R3B_*`: sin etiqueta de B; 14 lotes, esfuerzo bajo de los agentes) y el desempate de los 1,917 desacuerdos restantes (`lote_R3C_*`, 5 lotes). Todo con agentes Haiku 5.5 a ciegas (**anotadores del mismo modelo: errores correlacionados, sin validación humana**).
Resultado (`reports/improvement/consolidado_ronda3.md`): 26,011 textos → 24,007 consenso A = B, 1,898 consenso con C, 106 sin consenso (se excluyen). κ A–B = 0.844. Los lotes de rescate de A tuvieron menos acuerdo con B (82–90 %) que los de B con A (92–95 %); C no favoreció a ningún anotador (979 con A, 919 con B).
Jerga: 470 textos anotados; 41 se excluyen del entrenamiento (`pais_dudoso=1` o marcas de México/España) y «achis» se limita a 80. **Entran 271: 153 No Tóxico y 103 Ofensivo** (objetivo del plan: ≥ 300 y ≥ 100; No Tóxico no se alcanza).
Dataset v1.9.0: `build_dataset_final.py` con la política `RONDA3`. El banco congelado y val/test/batería quedan idénticos.
