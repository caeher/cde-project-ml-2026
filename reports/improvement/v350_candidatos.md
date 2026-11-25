# Ronda 3: candidatos frente a v3.4.0 (banco congelado n = 1391, test oficial n = 460)

| Modelo | F1 banco [IC 95 %] | Rec. Odio | Rec. Amenazas | F1 Amenazas | FPR NT | Test F1 | FPR NT jerga (test) | Afect./Ins. | T |
|---|---|---|---|---|---|---|---|---|---|
| v3.4.0 | 0.720 [0.687, 0.754] | 0.669 | 0.470 | 0.585 | 0.112 | 0.832 | 0.379 (n=29) | 18/20 · 17/18 | 1.58 |
| v3.5.0-rc1-sel | 0.736 [0.703, 0.766] | 0.615 | 0.590 | 0.683 | 0.124 | 0.829 | 0.310 (n=29) | 16/20 · 18/18 | 1.54 |
| profR3 | 0.749 [0.718, 0.779] | 0.654 | 0.624 | 0.709 | 0.127 | 0.832 | 0.345 (n=29) | 16/20 · 18/18 | 1.89 |

## Criterios del plan (fijados antes de entrenar)

### v3.5.0-rc1-sel
ΔF1 banco +0.0152 IC [-0.008, +0.040] · McNemar b/c 60/55 p = 0.7093 · ΔF1 Amenazas IC [+0.044, +0.156]

- ✔ 1a recall Amenazas ≥ 0.55
- ✔ 1b ΔF1 Amenazas IC > 0
- ✘ 2 FPR NT con jerga (test) ≤ 0.24
- ✔ 3a F1 banco no baja > 0.01
- ✘ 3b test oficial ≥ 0.83
- ✘ 3c FPR global ≤ 0.12
- ✘ 3d afectivas ≥ 17 e insultos ≥ 16
- ✘ 3e recall Odio no baja > 0.03

**NO se adopta** (3/8)

### profR3
ΔF1 banco +0.0288 IC [+0.004, +0.054] · McNemar b/c 67/54 p = 0.2753 · ΔF1 Amenazas IC [+0.064, +0.188]

- ✔ 1a recall Amenazas ≥ 0.55
- ✔ 1b ΔF1 Amenazas IC > 0
- ✘ 2 FPR NT con jerga (test) ≤ 0.24
- ✔ 3a F1 banco no baja > 0.01
- ✔ 3b test oficial ≥ 0.83
- ✘ 3c FPR global ≤ 0.12
- ✘ 3d afectivas ≥ 17 e insultos ≥ 16
- ✔ 3e recall Odio no baja > 0.03

**NO se adopta** (5/8)

Nota: la reserva `jerga_dev` no se apartó en el dataset v1.9.0; el criterio 2 usa solo el test oficial.