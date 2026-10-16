# Candidatos frente a la línea base (banco congelado n = 1391)

| Modelo | F1-macro [IC 95 %] | Recall Odio | Recall Amenazas | Recall Ofensivo | FPR (NT) | Test oficial F1 | Afectivas / Insultos | T |
|---|---|---|---|---|---|---|---|---|
| v3.3.0 | 0.693 [0.659, 0.726] | 0.577 | 0.487 | 0.796 | 0.129 | 0.839 | 19/20 · 18/18 | 1.31 |
| candC | 0.716 [0.683, 0.749] | 0.608 | 0.470 | 0.827 | 0.109 | 0.840 | 19/20 · 18/18 | 2.04 |
| sB_42 | 0.720 [0.687, 0.754] | 0.669 | 0.470 | 0.813 | 0.112 | 0.832 | 18/20 · 17/18 | 1.58 |
| sB_1337 | 0.707 [0.674, 0.740] | 0.585 | 0.496 | 0.792 | 0.112 | 0.821 | 19/20 · 18/18 | 1.60 |
| sB_2026 | 0.723 [0.691, 0.755] | 0.623 | 0.504 | 0.813 | 0.110 | 0.823 | 18/20 · 18/18 | 1.56 |
| studentB | 0.720 [0.687, 0.754] | 0.669 | 0.470 | 0.813 | 0.112 | 0.832 | 18/20 · 17/18 | 1.58 |

Pareado contra v3.3.0 (banco):

- candC: ΔF1 +0.0234 IC [-0.005, +0.052] · McNemar b/c 79/51 p = 0.0175
- sB_42: ΔF1 +0.0277 IC [-0.002, +0.056] · McNemar b/c 85/56 p = 0.0181
- sB_1337: ΔF1 +0.0142 IC [-0.014, +0.041] · McNemar b/c 72/57 p = 0.2176
- sB_2026: ΔF1 +0.0300 IC [+0.003, +0.058] · McNemar b/c 85/56 p = 0.0181
- studentB: ΔF1 +0.0277 IC [-0.002, +0.056] · McNemar b/c 85/56 p = 0.0181

Metas (recall Odio ≥ 0.65, Amenazas ≥ 0.60, FPR ≤ 0.12, F1 banco ≥ 0.70, test ≥ 0.83, afectivas ≥ 17, insultos ≥ 16):

- v3.3.0: Odio ✘ · Amenazas ✘ · FPR ✘ · F1 ✘ · test ✔ · afect ✔ · insultos ✔  (3/7)
- candC: Odio ✘ · Amenazas ✘ · FPR ✔ · F1 ✔ · test ✔ · afect ✔ · insultos ✔  (5/7)
- sB_42: Odio ✔ · Amenazas ✘ · FPR ✔ · F1 ✔ · test ✔ · afect ✔ · insultos ✔  (6/7)
- sB_1337: Odio ✘ · Amenazas ✘ · FPR ✔ · F1 ✔ · test ✘ · afect ✔ · insultos ✔  (4/7)
- sB_2026: Odio ✘ · Amenazas ✘ · FPR ✔ · F1 ✔ · test ✘ · afect ✔ · insultos ✔  (4/7)
- studentB: Odio ✔ · Amenazas ✘ · FPR ✔ · F1 ✔ · test ✔ · afect ✔ · insultos ✔  (6/7)