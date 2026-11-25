# Dataset v2.0.0: candidatos frente a mbert_v2

Test principal = test_hilos (n = 1975) + banco congelado (n = 1391). Temperatura en val_v2 (n = 2773).

| Modelo | F1 principal [IC 95 %] | Rec. NT / OF / OD / AM | FPR | F1 test_hilos | F1 banco | FPR jerga | Test oficial | Afect./Ins. | T |
|---|---|---|---|---|---|---|---|---|---|
| mbert_v2 | 0.642 [0.618, 0.664] | 0.84 / 0.70 / 0.52 / 0.63 | 0.157 | 0.602 | 0.639 | 0.149 (n=47) | 0.808 | 12/20 · 18/18 | 1.37 |

## Criterios (fijados antes de entrenar)
