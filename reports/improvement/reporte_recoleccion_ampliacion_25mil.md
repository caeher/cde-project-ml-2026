# Ronda 3, tramo hasta 25 mil: informe de recolección (29 de octubre de 2026)

Ampliación del [informe de la ronda 3](reporte_recoleccion_ronda3.md) (3,275 textos en 15 hilos). Mismo método: BrowserOS neo, solo lectura de respuestas públicas en X; no hubo respuestas, likes, reposts ni follows, no se inició sesión y no se etiquetó nada.

## Resultado
| Concepto | Valor |
|---|---|
| Textos en `data/sources/x_threads/phase3/` | **25,541** (meta: 25,000) |
| Hilos (archivos) | 109: 15 de la ronda 3 original y 94 nuevos |
| Grupo A (celebración, apología o deseo de daño) | 9,405 |
| Grupo B (conversación casual con jerga) | 7,143 |
| Grupo C (crítica política) | 8,993 |
| Duplicados en la pasada final sobre los 109 archivos juntos | 0 (código 0; `reports/improvement/dup_ampliacion_25mil_final2.csv`) |
| Ids de la ronda | `P3-00001` a `P3-26316` (hay huecos por textos quitados y hilos descartados) |

Los 15 hilos de la ronda 3 original siguen en su informe. Los 94 nuevos están abajo y todos están registrados en [REGISTRO.md](../../data/annotation/threads/REGISTRO.md).

## Cómo se llegó a 25 mil
- Los hilos se buscaron con `min_replies` (150 a 250 respuestas visibles) y, después de cada búsqueda, se abrieron tres hilos a la vez. Cada colector se detuvo al quedar sin respuestas nuevas durante 12 ticks, o al llegar a 480 elementos o 500 iteraciones.
- Cada hilo se limpió igual que en la ronda 3: sin menciones ni URL, español, al menos 4 palabras, sin repetidos dentro del hilo. Después se corrió `verificar_duplicados.py` contra todos los CSV del proyecto y se repitió hasta código 0.
- Se descartaron 5 hilos con menos de 120 respuestas útiles: B21 (115), B24 (105), B25 (105), B30 (52) y B38 (105). Quedaron en el scratchpad, no en `data/`.

## Limpieza y privacidad, pasada final
- Restos de enlaces (`.html`, rutas con fecha, `status/…?t=…&s=19`, `utm_`) en unos 150 textos: se quitaron esos fragmentos y se dejó el resto del texto. Se descartaron 3 que quedaron con menos de 4 palabras.
- 8 textos nombraban a una hija menor de edad de una pareja presidencial (un nombre de niña en tres hilos de aniversario y en uno de A28). Se quitaron por la regla de menores.
- 1 casi duplicado («Si totalmente de acuerdo», similitud 0.86 con el dataset de referencia) se quitó y la verificación final dio 0.
- Revisión aleatoria de 40 textos (semilla 2026) sobre el corpus completo: ninguno identifica a un particular. Búsqueda de teléfonos, correos y DUI: 0 correos, 0 DUI y ningún teléfono real después de quitar el número que ya se había eliminado (P3-08527).
- Las figuras públicas (funcionarios, periodistas, deportistas, diputados) se conservan: son el objeto de los hilos.

## Hilos nuevos
| Archivo | Tema | Grupo | Id de publicación | Textos finales |
|---|---|---|---|---|
| A10_tercer_aniversario_regimen.csv | tercer aniversario regimen | A | 1905449849614459355 | 239 |
| A11_casi_600_capturas.csv | casi 600 capturas | A | 1508270604872523779 | 280 |
| A12_emma_dejar_morir_hambre.csv | emma dejar morir hambre | A | 1689712820584148992 | 271 |
| A13_megacarcel_12000.csv | megacarcel 12000 | A | 1716152583650234520 | 290 |
| A14_movilizacion_70.csv | movilizacion 70 | A | 1686412797222014976 | 148 |
| A15_duro_golpe_pandilleros.csv | duro golpe pandilleros | A | 1658848030928302080 | 223 |
| A16_cecot_pandilleros_esto_es.csv | cecot pandilleros esto es | A | 1945269189549113453 | 207 |
| A17_solicito_regimen_asamblea.csv | solicito regimen asamblea | A | 1507901269138194433 | 256 |
| A18_cena_navidad_cecot.csv | cena navidad cecot | A | 1740780091993374915 | 305 |
| A19_convoca_consejo_ministros.csv | convoca consejo ministros | A | 1518083575467368449 | 274 |
| A1_capturas_4_dias.csv | capturas 4 dias | A | 1509018006432665600 | 258 |
| A1_mensaje_criminales.csv | mensaje criminales | A | 1511160179135586308 | 245 |
| A20_brutal_venganza.csv | brutal venganza | A | 1766960948806385805 | 136 |
| A21_te_gustaria_delincuentes.csv | te gustaria delincuentes | A | 1654532026576388097 | 190 |
| A22_mega_carcel_40000.csv | mega carcel 40000 | A | 1620753971831836672 | 217 |
| A23_ropa_interior.csv | ropa interior | A | 1255390132078882816 | 317 |
| A24_mano_dura.csv | mano dura | A | 1636112372531118080 | 249 |
| A25_duro_golpe_criminales.csv | duro golpe criminales | A | 1666658433230155779 | 210 |
| A26_ocho_reclusos.csv | ocho reclusos | A | 1630192992815394818 | 274 |
| A27_candidato_arena_carcel.csv | candidato arena carcel | A | 1680727722539065344 | 304 |
| A28_criminales_carcel.csv | criminales carcel | A | 1570167309691662338 | 142 |
| A29_sobreviviente_terror.csv | sobreviviente terror | A | 1658506334512328705 | 235 |
| A30_segundo_grupo_traslado.csv | segundo grupo traslado | A | 1636074901684494337 | 282 |
| A31_cecot_familia.csv | cecot familia | A | 2000960861410603172 | 274 |
| A32_pandilleros_cecot_piensan.csv | pandilleros cecot piensan | A | 1639527660983336962 | 160 |
| A33_madrugada_ejecuta.csv | madrugada ejecuta | A | 1629249512337293315 | 214 |
| A34_regimen_se_rien.csv | regimen se rien | A | 1698010558048370871 | 154 |
| A35_confinamiento_terrorismo.csv | confinamiento terrorismo | A | 1620752336556523522 | 207 |
| A36_mega_carcel_mensaje.csv | mega carcel mensaje | A | 1620863483553394689 | 252 |
| A5_familiares_detenidos.csv | familiares detenidos | A | 1625166717449121792 | 308 |
| A6_criminalidad_bukele.csv | criminalidad bukele | A | 1615892766730469376 | 211 |
| A7_un_anio_regimen.csv | un anio regimen | A | 1640469676458164226 | 254 |
| A8_agente_asesinado.csv | agente asesinado | A | 1658844243677310977 | 256 |
| A9_capturas_8000.csv | capturas 8000 | A | 1512325092059095040 | 270 |
| B10_pupusas_mesoamericanas.csv | pupusas mesoamericanas | B | 1962279517377949825 | 309 |
| B11_chivo_wallet.csv | chivo wallet | B | 1757175168076480959 | 122 |
| B12_bitcoin_perdidas.csv | bitcoin perdidas | B | 1855967978732347895 | 140 |
| B13_derrota_guatemala.csv | derrota guatemala | B | 2104788141144264815 | 273 |
| B14_partido_puerto_rico.csv | partido puerto rico | B | 1798937686641967201 | 265 |
| B15_ricky_messi.csv | ricky messi | B | 1748411414807454154 | 216 |
| B16_aficionado_lagrimas.csv | aficionado lagrimas | B | 1965284913600487585 | 154 |
| B17_dt_no_es_fracaso.csv | dt no es fracaso | B | 1978324743645204642 | 234 |
| B18_aficionados_fito.csv | aficionados fito | B | 1669374081370562560 | 135 |
| B19_kurupi_millonario.csv | kurupi millonario | B | 2043038053246140803 | 141 |
| B20_proponen_fito.csv | proponen fito | B | 1701643948962238699 | 204 |
| B22_necesita_aficion.csv | necesita aficion | B | 1937740141230956889 | 142 |
| B23_bienvenido_bolillo.csv | bienvenido bolillo | B | 1894184256450220538 | 153 |
| B26_encuesta_selecta_vergonzoso.csv | encuesta selecta vergonzoso | B | 2104770480825913735 | 191 |
| B27_selecta_hasta_aca.csv | selecta hasta aca | B | 1419106929289408515 | 297 |
| B28_selecta_san_vicente.csv | selecta san vicente | B | 1845644179054985687 | 194 |
| B29_tenemos_selecta.csv | tenemos selecta | B | 1419107392504086532 | 259 |
| B31_jairo_empate.csv | jairo empate | B | 1798942561887015037 | 167 |
| B32_rubén_botada.csv | rubén botada | B | 1736907286847648094 | 132 |
| B33_alcalde_pupuseria.csv | alcalde pupuseria | B | 1320716478186987521 | 282 |
| B34_albos_emplumados.csv | albos emplumados | B | 1824132038162543078 | 129 |
| B35_zavaleta_roldan.csv | zavaleta roldan | B | 1716969400195043470 | 276 |
| B36_concierto_cuscatlan.csv | concierto cuscatlan | B | 1964478689678414199 | 302 |
| B37_experimentados_selecta.csv | experimentados selecta | B | 1706363459166691592 | 123 |
| B7_intolerancia_calle.csv | intolerancia calle | B | 1586820581668052992 | 292 |
| B8_yeik_creador.csv | yeik creador | B | 2023228871374467408 | 329 |
| B9_censo_hinchas.csv | censo hinchas | B | 2028597746500792404 | 122 |
| C10_pasaje_un_dolar.csv | pasaje un dolar | C | 1980345257607754160 | 255 |
| C11_estadio_china.csv | estadio china | C | 1202580805505224705 | 302 |
| C12_bukele_fe.csv | bukele fe | C | 2114341207258316912 | 216 |
| C13_mesas_suspendidas.csv | mesas suspendidas | C | 1239993268160643078 | 298 |
| C14_uci_hospital.csv | uci hospital | C | 1570604027595083778 | 160 |
| C15_ningun_salvadoreno_haiti.csv | ningun salvadoreno haiti | C | 1928126228608733693 | 256 |
| C16_elecciones_encuestas.csv | elecciones encuestas | C | 1753833738629181949 | 285 |
| C17_oposicion_gobierno.csv | oposicion gobierno | C | 1816947731044417730 | 248 |
| C18_bukele_haiti.csv | bukele haiti | C | 2114336027976278422 | 237 |
| C19_opositores_actos.csv | opositores actos | C | 1835405868998779072 | 326 |
| C20_diputadas_oposicion.csv | diputadas oposicion | C | 1748980898677039124 | 200 |
| C21_guerra_corruptos.csv | guerra corruptos | C | 1665297340180185089 | 183 |
| C22_nTN24_carcel_polemica.csv | nTN24 carcel polemica | C | 1630304209160601601 | 318 |
| C23_tratos_inhumanos.csv | tratos inhumanos | C | 1638151784731488259 | 224 |
| C24_cola_bukele.csv | cola bukele | C | 2114156780636827803 | 236 |
| C25_apoyar_bukele.csv | apoyar bukele | C | 1841526343860650049 | 308 |
| C26_no_encarcelamos_oposicion.csv | no encarcelamos oposicion | C | 1838674900917313938 | 240 |
| C27_mensaje_prensa.csv | mensaje prensa | C | 1673118417811800066 | 272 |
| C28_analista_oposicion.csv | analista oposicion | C | 1974187926679666773 | 279 |
| C29_reeleccion_indefinida.csv | reeleccion indefinida | C | 1975005620404392433 | 286 |
| C30_indefinida_zavala.csv | indefinida zavala | C | 1918108599114457585 | 270 |
| C31_lorena_pena_movilizacion.csv | lorena pena movilizacion | C | 1680943994971250690 | 127 |
| C32_jaime_bayly.csv | jaime bayly | C | 1754856308635746466 | 162 |
| C34_elfaro_peores_tradiciones.csv | elfaro peores tradiciones | C | 1754550768298868745 | 248 |
| C35_dictador_amparo.csv | dictador amparo | C | 2071713208659046797 | 328 |
| C36_david_qva_maduro.csv | david qva maduro | C | 1878184453429760387 | 326 |
| C3_oposicion_regimen_popular.csv | oposicion regimen popular | C | 1566960564819169281 | 265 |
| C4_oposicion_mentira.csv | oposicion mentira | C | 1752493262667915372 | 281 |
| C5_dejen_de_discutir.csv | dejen de discutir | C | 1278186070312652800 | 314 |
| C6_muchas_personas_no_entienden.csv | muchas personas no entienden | C | 1821761488656253080 | 283 |
| C7_mexicano_dictadura.csv | mexicano dictadura | C | 1877762671073759651 | 311 |
| C8_director_arriaza.csv | director arriaza | C | 1833033998248943641 | 266 |
| C9_navidad_gasolina.csv | navidad gasolina | C | 1739277427229016329 | 268 |

## Incidencias
- **Pestaña equivocada:** una pestaña de notificaciones terminó en `/notifications`. Ese volcado se descartó antes de guardar nada y el hilo se recolectó otra vez.
- **Errores del navegador:** varias ejecuciones dieron `group_out_of_scope`, `target_scope_unsupported` o pasaron de 30 s. Se recuperaron abriendo pestañas nuevas y repitiendo la espera; ningún colector se perdió.
- **Duplicados mal emparejados:** `quitar_dups.py` no encontraba textos que la tabla guarda truncados a 90 caracteres. Se cambió a comparación normalizada con respaldo por prefijo, y en dos hilos (C3 y C20) se quitaron filas por id.
- **Bitácora incompleta:** el registro de lotes (`bitacora.csv`, en el scratchpad) no guardó las filas de los lotes 27 a 32. Los ids de esos hilos se reconstruyeron de los lotes ejecutados y están verificados contra cada archivo.
- **Pestañas:** se cerraron las pestañas de búsqueda y colección ya volcadas.

## Limitaciones
- **Balance de grupos.** El tramo hace subir C a 35 % del total (A 37 %, B 28 %). La búsqueda de B con jerga se agotó pronto; B siguió creciendo con hilos de fútbol y con dos hilos de vida cotidiana. Los hilos de C se eligieron por volumen, y en X la mayoría de respuestas políticas son hostiles o de defensa del gobierno. El criterio de «crítica sin insultos» no se verificó por contenido.
- **Jerga.** No se midió en el tramo nuevo. La cifra de 161 textos con jerga de la ronda 3 sigue siendo la única cota.
- **Grupos y subgrupos** son provisionales: vienen del hilo de origen, no de una etiqueta. Las etiquetas las pondrán los anotadores.
- **Dependencia de los ids:** un mismo tuit de Bukele o de Menoni puede tener respuestas que se repiten en hilos distintos. La verificación cubre duplicados exactos y casi duplicados, pero no plantillas de respuesta.
- **Techo de X:** cada hilo carga entre ~120 y ~480 respuestas; por eso el tamaño por hilo oscila.
- **Alcance.** 25,000 es ocho veces el encargo original de 3,000. Se mantuvieron las reglas de lectura, las esperas explícitas y el límite de tres páginas por ejecución.
