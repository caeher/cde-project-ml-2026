# Consolidado de la ronda 3 (anotación a ciegas)

Generado por `src/data/threads/consolidar_ronda3.py`. Textos recolectados con BrowserOS (respuestas públicas de X, sin usuarios); etiquetas de agentes Haiku 5.5 con la guía v2.0: A lee la guía completa, B trabaja con un resumen; C desempata a ciegas solo los desacuerdos. **Todos los anotadores son LLM del mismo modelo: errores correlacionados, sin validación humana.**

## Estado de los textos

| Estado | Textos |
|---|---|
| consenso | 20,423 |
| sin_anotar | 2,614 |
| desacuerdo_pendiente | 1,582 |
| un_anotador | 1,305 |
| consenso_c | 83 |
| sin_consenso | 4 |

Total: **26,011** textos (25,541 de hilos de la ronda 3 y 470 de la búsqueda de jerga).

## Acuerdo entre A y B (22,092 textos con las dos etiquetas)

- κ de Cohen = **0.848** (umbral de la guía: 0.60); acuerdo = 0.924.
- Acuerdo por lote: mínimo 0.889, mediana 0.926, máximo 0.960.
- κ de la clase No Tóxico: 0.867
- κ de la clase Ofensivo: 0.848
- κ de la clase Odio: 0.714
- κ de la clase Amenazas: 0.808

## Textos con consenso por grupo y clase

| Grupo | No Tóxico | Ofensivo | Odio | Amenazas | Total |
|---|---|---|---|---|---|
| A | 5,361 | 1,319 | 36 | 832 | 7,548 |
| B | 3,596 | 2,068 | 72 | 61 | 5,797 |
| C | 4,760 | 2,115 | 155 | 131 | 7,161 |
| **Total** | **13,717** | **5,502** | **263** | **1,024** | **20,506** |

Con jerga (léxico amplio, `JERGA` en el script): **249** No Tóxico y **473** Ofensivo con consenso. El plan de la ronda 3 pedía ≥ 300 No Tóxico con jerga; el léxico amplio incluye términos que también se usan fuera de El Salvador.

## Lotes

- Anotados por A y B sin faltantes: 40 de 52.
- Sin desempate C todavía: 1,582 textos (la anotación se cortó por el límite de gasto; se reanuda con el mismo flujo, que reutiliza lo ya hecho).

## Advertencias

- **La jerga recolectada es poca y de calidad dudosa:** 470 textos en 8 términos, 57 % de un solo término («achis»), con contenido de México y España y nombres propios («jana», «chulón»). No pasaron por anotación; no usar para entrenar sin revisarlos.
- Los desacuerdos pendientes son los casos más difíciles; excluirlos sesga la muestra hacia lo fácil.
- Las etiquetas aún no entran al dataset: `build_dataset_final.py` solo lee `consenso_fase1_r*.csv`, así que **el dataset v1.8.0 y el banco congelado no cambian** hasta construir v1.9.0.
