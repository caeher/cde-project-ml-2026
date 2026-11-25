# Dataset v2.0.0: candidatos frente a v3.4.0

Test principal = test_hilos (n = 1975) + banco congelado (n = 1391). Temperatura en val_v2 (n = 2773).

| Modelo | F1 principal [IC 95 %] | Rec. NT / OF / OD / AM | FPR | F1 test_hilos | F1 banco | FPR jerga | Test oficial | Afect./Ins. | T |
|---|---|---|---|---|---|---|---|---|---|
| v3.4.0 | 0.708 [0.683, 0.731] | 0.90 / 0.79 / 0.61 / 0.54 | 0.097 | 0.638 | 0.720 | 0.128 (n=47) | 0.832 | 18/20 · 17/18 | 1.44 |
| profV2 | 0.745 [0.721, 0.767] | 0.90 / 0.84 / 0.61 / 0.67 | 0.103 | 0.722 | 0.732 | 0.085 (n=47) | 0.819 | 17/20 · 18/18 | 1.77 |
| v3.6.0-rc1-sel | 0.752 [0.728, 0.774] | 0.91 / 0.83 / 0.59 / 0.68 | 0.089 | 0.731 | 0.740 | 0.043 (n=47) | 0.827 | 17/20 · 18/18 | 1.41 |

Entrenados con v1.9.0 (vieron los hilos de test_hilos): solo banco congelado.

| Modelo | F1 banco | Test oficial | Afect./Ins. |
|---|---|---|---|
| profR3 | 0.749 | 0.832 | 16/20 · 18/18 |
| v3.5.0-rc1-sel | 0.736 | 0.829 | 16/20 · 18/18 |
| mbert-sv | 0.640 | 0.778 | 12/20 · 18/18 |

## Criterios (fijados antes de entrenar)

### profV2
ΔF1 principal +0.0366 IC [+0.018, +0.056] · McNemar b/c 175/115 p = 0.0005

- ✔ 1 ΔF1 principal IC > 0
- ✔ 2 FPR no sube > 0.01
- ✔ 3 recall Amenazas ≥ 0.55
- ✔ 4 recall Odio no baja > 0.03
- ✔ 5 afectivas ≥ 17 e insultos ≥ 16
- ✘ 6 test oficial ≥ 0.82
- ✔ 7 FPR jerga < referencia

**NO se adopta** (6/7)

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
