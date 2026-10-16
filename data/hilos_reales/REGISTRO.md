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

## Estructura de `data/hilos_reales/`
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

**Banco congelado** (`data/banco_congelado/`, SHA-256 en `MANIFEST.json`; nunca entra a entrenamiento ni a selección): `migrantes` (306), `externo2` (647), `militares_pandilleros` (202), `xenofobia_federico` (236) + test oficial (460).
**Pool de entrenamiento** (14 hilos): canje, cecot, feminismo, infierno_tierra, invasion, lgbt_bandera, lgbt_ultimahora, miss_el_salvador, pandilleros_traslado, racismo, racismo_orgullo, repatriados, trans, venezolanos2 → 2,698 filas (NT 1,493 · OF 673 · **OD 334 · AM 198**), con etiquetas blandas `p0..p3`. `data/dataset_final/train.csv` = 9,181 filas.
**Cuotas de la fase 1:** ≥ 700 Odio y ≥ 450 Amenazas con consenso (hoy 334 y 198).

## Fase 1 del plan de mejora — cerrada (17 de octubre de 2026)
Dos rondas de recolección dirigida con BrowserOS (18 hilos, 3,502 textos útiles tras quitar la publicación original y duplicados) y etiquetado por consenso: dos anotadores de **modelos distintos** (Sonnet y Opus) a ciegas + desempate con un tercer modelo.
- Ronda 1 (12 hilos, 2,115 textos): κ Sonnet–Opus = 0.771, 85.7 % de acuerdo, 302 desempates, 26 sin consenso.
- Ronda 2 (6 hilos de Odio, 1,387 textos): κ = 0.792, 86.7 % de acuerdo, 184 desempates, 16 sin consenso.
- Pool final: 32 hilos, 6,158 filas → **Odio 850 (cuota 700 ✓) · Amenazas 559 (cuota 450 ✓)**; `data/dataset_final/train.csv` = 12,641 filas.
- Limitación declarada: todos los anotadores son LLM (errores correlacionados); Opus es más estricto con insultos leves que Sonnet (534 vs 401 Ofensivo en la ronda 1). Un incidente de archivos temporales compartidos en la ronda 1 se corrigió exigiendo directorios propios.
