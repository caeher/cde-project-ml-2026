# Ronda 3: candidatos frente a v3.4.0 (banco congelado n = 1391, test oficial n = 460)

| Modelo | F1 banco [IC 95 %] | Rec. Odio | Rec. Amenazas | F1 Amenazas | FPR NT | Test F1 | FPR NT jerga (test) | Afect./Ins. | T |
|---|---|---|---|---|---|---|---|---|---|
| v3.4.0 | 0.720 [0.687, 0.754] | 0.669 | 0.470 | 0.585 | 0.112 | 0.832 | 0.379 (n=29) | 18/20 · 17/18 | 1.58 |
| mbert-sv | 0.640 [0.606, 0.674] | 0.469 | 0.590 | 0.566 | 0.149 | 0.778 | 0.379 (n=29) | 12/20 · 18/18 | 2.28 |

## Criterios del plan (fijados antes de entrenar)

### mbert-sv
ΔF1 banco -0.0802 IC [-0.115, -0.045] · McNemar b/c 94/185 p = 0.0000 · ΔF1 Amenazas IC [-0.101, +0.061]

- ✔ 1a recall Amenazas ≥ 0.55
- ✘ 1b ΔF1 Amenazas IC > 0
- ✘ 2 FPR NT con jerga (test) ≤ 0.24
- ✘ 3a F1 banco no baja > 0.01
- ✘ 3b test oficial ≥ 0.83
- ✘ 3c FPR global ≤ 0.12
- ✘ 3d afectivas ≥ 17 e insultos ≥ 16
- ✘ 3e recall Odio no baja > 0.03

**NO se adopta** (1/8)

Nota: la reserva `jerga_dev` no se apartó en el dataset v1.9.0; el criterio 2 usa solo el test oficial.