# Dataset v4 — Etapa II + datos reales de X (octubre 2026)

**Versión 2** · 7 de octubre de 2026 · normalizador **v1.2** · base: train de la Etapa II (repo v3)

Reconstruir (sin argumentos): `python src/data/build_dataset_v4.py`

La versión 1 (base B2, normalizador v1.1) quedó archivada en
`archivo/2026-10-07_v4_normalizacion_v1.1/`. La comparación entre ambas está en
`logs/2026-10-07_comparacion_v4_v1.1_vs_v1.2.log`.

## Qué cambió respecto de la versión 1

| | v1 (archivada) | **v2 (esta)** |
|---|---|---|
| Train base | B2 (3,293) | **Etapa II, `data/dataset_v3/train.csv` (6,416)** |
| Normalizador | v1.1 | **v1.2**, el de la Etapa II: no rompe la ofuscación con arroba (`m@ldito`) y traduce 🔫 como `:pistola:` |
| Filas de octubre incorporadas | 4,074 | 4,074 (las mismas, con la misma etiqueta) |
| `texto_modelo` distinto en las de octubre | — | 7 de 4,074 (`reports/v4_diff_normalizacion_v1.1_v1.2.csv`) |
| Filas de la base quitadas por solapar con val, test o batería | 23 | 21 |
| Train total | 7,344 | **10,469** |

val, test y batería no cambian: son byte a byte los de julio (SHA-256 del test `5d1284efcc7df20f`).
Huella de contenido del train (ID, texto_original, texto_modelo, label, origen): `36617f83838f77c3`.
Es la misma reconstruyendo en la PC y en la nube.

## Qué entró

| | Filas |
|---|---|
| Recibidas en `data/new-10-7-2026/` | 4,328 |
| Ya estaban en **val, test o la batería** | −80 |
| Conflicto de etiqueta entre anotadores | 0 |
| Duplicados internos | −6 |
| Ya presentes en el train base | −168 |
| **Incorporadas** | **4,074** |

Además se quitaron **21 filas del train de la Etapa II**: 1 coincidía con val y 20 sintéticos repetían una
frase de la batería adversarial con otro emoji. **El test no tenía solape.** La batería de la Etapa II
(127/144) sí pudo estar favorecida por esas 20 filas.

La verificación final aborta si algún texto de train coincide con val, test o la batería, comparando
tanto el texto crudo como el normalizado.

> La versión 1 de este README decía «−6 por conflicto, −3 duplicados». El script nunca produjo esas cifras:
> son 0 y 6. El total de 4,074 sí era correcto.

## Corrección de etiquetas

**384 filas de `thenewdata_X.csv` se reetiquetaron de Discurso de Odio a Lenguaje Ofensivo**: insultos por
afiliación política (ARENA, FMLN, Nuevas Ideas). La guía (§3.1) dice que la afiliación política no es
categoría protegida.

## Composición

| Origen | No Tóxico | Ofensivo | Odio | Amenazas | Total |
|---|---|---|---|---|---|
| Real (Etapa II) | 570 | 742 | 442 | 389 | 2,143 |
| Sintético (B2 + v3) | 1,218 | 1,036 | 1,238 | 760 | 4,252 |
| Octubre (X) | 795 | 1,709 | 613 | 957 | 4,074 |
| **Total** | **2,583** | **3,487** | **2,293** | **2,106** | **10,469** |

Pesos por clase (len / 4·n): `[1.0133, 0.7506, 1.1414, 1.2428]`.

Columnas añadidas: `recolector`, `validado` (las de octubre vienen en `NO`), `fuera_de_sv` (230 filas sin
señal salvadoreña, para la ablación `--excluir_fuera_sv`). `URL_Original` se eliminó.

## Entrenamiento

`notebooks/03_reentrenar_v4_colab.ipynb` corre dos veces la receta de la Etapa II sobre este archivo:
con las filas de octubre (`--peso_nuevos 1.0`) y sin ellas (`--peso_nuevos 0.0`, 6,395 filas), mismas
semillas, y compara con McNemar pareado y bootstrap.

## Prueba con modelo lineal — medida sobre la versión 1, no rehecha

TF-IDF + LinearSVC, train B2 frente a v4-v1. **No se repitió sobre esta versión**:

| Train | F1 test | X (n=228) | Facebook (n=232) |
|---|---|---|---|
| B2 (sin nuevos) | 0.7808 | 0.866 | 0.659 |
| v4-v1 (con nuevos) | 0.7733 | 0.889 | 0.611 |

## Advertencias para la tesina

1. **Etiquetas preliminares:** las 4,074 de octubre tienen `Validado = NO`; no hubo segundo anotador.
2. **Cada archivo es de una sola clase y viene de búsquedas por palabra clave.** Existe el riesgo de que el
   modelo aprenda el estilo de la consulta en vez del contenido.
3. **Son 100 % de X.** No atacan el punto débil (Facebook).
