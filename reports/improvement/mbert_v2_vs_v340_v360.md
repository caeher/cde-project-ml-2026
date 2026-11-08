# Dataset v2.0.0: candidatos frente a v3.4.0

Test principal = test_hilos (n = 1975) + banco congelado (n = 1391). Temperatura en val_v2 (n = 2773).

| Modelo | F1 principal [IC 95 %] | Rec. NT / OF / OD / AM | FPR | F1 test_hilos | F1 banco | FPR jerga | Test oficial | Afect./Ins. | T |
|---|---|---|---|---|---|---|---|---|---|
| v3.4.0 | 0.708 [0.683, 0.731] | 0.90 / 0.79 / 0.61 / 0.54 | 0.097 | 0.638 | 0.720 | 0.128 (n=47) | 0.832 | 18/20 · 17/18 | 1.44 |
| mbert_v2 | 0.642 [0.619, 0.664] | 0.84 / 0.70 / 0.52 / 0.63 | 0.157 | 0.602 | 0.639 | 0.149 (n=47) | 0.808 | 12/20 · 18/18 | 1.37 |
| v3.6.0-rc1-sel | 0.752 [0.728, 0.774] | 0.91 / 0.83 / 0.59 / 0.68 | 0.089 | 0.731 | 0.740 | 0.043 (n=47) | 0.827 | 17/20 · 18/18 | 1.41 |

## Criterios (fijados antes de entrenar)

### mbert_v2
ΔF1 principal -0.0660 IC [-0.091, -0.040] · McNemar b/c 227/420 p = 0.0000

- ✘ 1 ΔF1 principal IC > 0
- ✘ 2 FPR no sube > 0.01
- ✔ 3 recall Amenazas ≥ 0.55
- ✘ 4 recall Odio no baja > 0.03
- ✘ 5 afectivas ≥ 17 e insultos ≥ 16
- ✘ 6 test oficial ≥ 0.82
- ✘ 7 FPR jerga < referencia

**NO se adopta** (1/7)

### v3.6.0-rc1-sel
ΔF1 principal +0.0443 IC [+0.025, +0.064] · McNemar b/c 182/100 p = 0.0000

- ✔ 1 ΔF1 principal IC > 0
- ✔ 2 FPR no sube > 0.01
- ✔ 3 recall Amenazas ≥ 0.55
- ✔ 4 recall Odio no baja > 0.03
- ✔ 5 afectivas ≥ 17 e insultos ≥ 16
- ✔ 6 test oficial ≥ 0.82
- ✔ 7 FPR jerga < referencia

**SE ADOPTA** (7/7)
