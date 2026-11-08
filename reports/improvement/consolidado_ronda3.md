# Consolidado de la ronda 3 (anotación a ciegas)

Generado por `src/data/threads/consolidar_ronda3.py`. Textos recolectados con BrowserOS (respuestas públicas de X, sin usuarios); etiquetas con la guía v2.0 por **Cristian** (guía completa, columna A), **Willian** (resumen, columna B) y **Julio** (desempate, columna C).

## Estado de los textos

| Estado | Textos |
|---|---|
| consenso | 24,007 |
| consenso_c | 1,898 |
| sin_consenso | 106 |

Total: **26,011** textos (25,541 de hilos de la ronda 3 y 470 de la búsqueda de jerga).

## Acuerdo entre A y B (26,011 textos con las dos etiquetas)

- κ de Cohen = **0.844** (umbral de la guía: 0.60); acuerdo = 0.923.
- Acuerdo por lote: mínimo 0.876, mediana 0.926, máximo 0.958.
- κ de la clase No Tóxico: 0.863
- κ de la clase Ofensivo: 0.845
- κ de la clase Odio: 0.713
- κ de la clase Amenazas: 0.797

## Textos con consenso por grupo y clase

| Grupo | No Tóxico | Ofensivo | Odio | Amenazas | Total |
|---|---|---|---|---|---|
| A | 6,454 | 1,773 | 51 | 1,071 | 9,349 |
| B | 4,352 | 2,595 | 97 | 85 | 7,129 |
| B2 | 327 | 125 | 14 | 3 | 469 |
| C | 5,757 | 2,768 | 240 | 193 | 8,958 |
| **Total** | **16,890** | **7,261** | **402** | **1,352** | **25,905** |

Con jerga (léxico amplio, `JERGA` en el script): **616** No Tóxico y **739** Ofensivo con consenso. El plan de la ronda 3 pedía ≥ 300 No Tóxico con jerga; el léxico amplio incluye términos que también se usan fuera de El Salvador.

## Lotes y desempate

- Lotes de origen con A y B completos: 52 de 52; el resto se completó con lotes de rescate (`lote_R3A_*`, `lote_R3B_*`).
- Desempatados por C: 2,004 textos. Pendientes de desempate: 0. Sin consenso (A, B y C distintos): 106, que no se usan.
- C marcó seguro=0 en la mayoría de los desacuerdos (son los casos más difíciles): las etiquetas de `consenso_c` son más ruidosas; en el dataset llevan etiqueta blanda (2 de 3 votos).

## Advertencias

- **La jerga recolectada es poca y de calidad dudosa:** 470 textos en 8 términos, 57 % de un solo término («achis»), con contenido de México y España y nombres propios («jana», «chulón»). En el dataset v1.9.0 se excluyen los marcados `pais_dudoso=1` y los textos con marcas de México o España, y «achis» se limita a 80 textos (`RONDA3` en `src/data/build_dataset_final.py`).
- Los textos sin consenso quedan fuera; excluirlos sesga la muestra hacia lo fácil.
- El desacuerdo residual entre anotadores (κ reportado) acota la calidad de la etiqueta.
- El dataset v1.9.0 incorpora estas etiquetas con la política de balance `RONDA3` (todas las Amenazas y el Odio; tope por hilo de No Tóxico y Ofensivo). El banco congelado y el conjunto de val y test no cambian.
