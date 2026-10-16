# Archivo — dataset v4, versión 1 (normalizador v1.1)

Archivado el 7 de octubre de 2026, al pasar a la versión 2 (normalizador v1.2, base Etapa II).
Nada de esta carpeta se usa para entrenar; se guarda solo para comparar.

| Archivo | Qué es |
|---|---|
| `dataset_v4/` → movido a `data/history/v1.3.0/` (16-oct-2026) | Dataset v4 original: base B2, 7,344 filas, `texto_modelo` con normalizador v1.1 |
| `src/normalization_v1.1.py` | Normalizador que estaba en la carpeta local (no es el de la Etapa II) |
| `src/build_dataset_v4_original.py` | Script de construcción tal como estaba |
| `src/entrenar_v4_original.py` | Entrenador original. **Defectuoso:** usaba `robertuito-base-uncased` en minúsculas (la Etapa II usó `-cased`) y dejaba con peso 1.0 los 3,132 sintéticos `v3_*` |
| `reports/` | Trazabilidad de la limpieza de la versión 1 (fugas y conflictos) |

Comparación con la versión 2:

- `logs/2026-10-07_comparacion_v4_v1.1_vs_v1.2.log`: composición, metadata y cambios de texto
- `logs/2026-10-07_diff_normalization_v1.1_v1.2.diff`: diferencias entre los dos normalizadores
- `reports/v4_diff_normalizacion_v1.1_v1.2.csv`: las 7 filas de octubre cuyo `texto_modelo` cambia

Resumen: las 4,074 filas de octubre y sus etiquetas son las mismas en las dos versiones. Cambian
la base (B2 de 3,293 → Etapa II de 6,416) y 7 textos normalizados.
