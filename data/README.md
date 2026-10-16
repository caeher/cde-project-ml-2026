# data/

Organizado por **propósito**, siguiendo el flujo del proyecto: lo recolectado → su anotación → el dataset → los conjuntos de evaluación. Las rutas en código se leen de `src/paths.py`.

```
data/
├── sources/                  lo recolectado, sin etiquetar
│   ├── stage1_corpus/        corpus salvadoreño y léxicos de la Etapa I        (privado: no se versiona)
│   ├── x_oct2026/            textos de X de octubre de 2026 (entraron en v1.3.x con peso 0)
│   ├── x_threads/            hilos reales de X recolectados con BrowserOS (respuestas, sin usuarios)
│   │   └── phase1/           hilos de la fase 1 del plan de mejora
│   └── external/             reservado
├── annotation/
│   ├── stage1/               anotación de la Etapa I: LLM, adjudicación, gold   (privado: no se versiona)
│   └── threads/              anotación de los hilos (guía v2.0, ver docs/guia_anotacion.md)
│       ├── blind/            lotes a ciegas (lote_*) y salidas de cada anotador (salida_*)
│       ├── labels/           consensos de 3 anotadores (consenso_*.csv) y sessions/ (etiquetado manual lab1–5)
│       ├── predictions/      predicciones de modelos sobre hilos (diagnóstico)
│       ├── review/           revisión de 125 casos (HTML)
│       ├── REGISTRO.md       qué hilo va al pool de entrenamiento y cuál al banco congelado
│       └── LEEME.md
├── dataset/                  ★ EL dataset vigente: dataset v1.8.0 (train/val/test/test_adversarial + metadata.json)
├── history/                  versiones anteriores, solo para reproducir cifras ya reportadas (ver history/VERSIONS.md)
│   └── v1.0.0/ … v1.7.0/
└── evaluation/               conjuntos que NUNCA entrenan ni deciden
    ├── frozen_bank/          banco congelado: 4 hilos con consenso + MANIFEST.json (SHA-256)
    └── hard_cases/           casos difíciles y sonda de vulgaridad afectiva (solo evaluar)
```

## Reglas
1. **Un solo dataset vigente** (`dataset/`). Lo genera un único script: `python src/data/build_dataset_final.py` (con `--selftest` comprueba que detecta fugas).
2. **El banco congelado y `hard_cases` no se tocan:** si cambian sus SHA-256 (`frozen_bank/MANIFEST.json`), las comparaciones dejan de ser válidas.
3. **Versiones del dataset:** semver propio (`dataset v1.x.x`), independiente del modelo (`v3.x.x`). Ver `history/VERSIONS.md`.
4. **Privacidad:** no se versionan usuarios ni enlaces a perfiles; `stage1_corpus/`, `annotation/stage1/` e `history/v1.0.0/` quedan fuera de git (`.gitignore`).

## Linaje
```
sources/stage1_corpus ─► annotation/stage1 ─► history/v1.0.0 ─► v1.1.0 ─► v1.2.0 ─┐
sources/x_oct2026 ─────────────────────────────────────────────────────────────► v1.3.0 ─► v1.3.1 ─┐
sources/x_threads ─► annotation/threads (blind → labels) ──────────────────────────────────────────┴► v1.4.0 … v1.7.0 ─► dataset (v1.8.0)
                                                    └─► evaluation/frozen_bank (hilos reservados)
```
