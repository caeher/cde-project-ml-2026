# Contrato de datos V3 (congelado)

**Procedencia:** rama `v3` @ `95d3ba63f40413e493cc0df174ea5b9cc2da7f47`  
**Uso en `main`:** `data/processed/v3/` es la única ruta soportada por `src/modeling_v3/`.

## Esquema

| Campo | Uso |
|-------|-----|
| `texto_modelo` | Entrada del tokenizador (texto normalizado v1.2) |
| `label` | Entero 0–3 (cuatro clases) |
| `origen` | `real` vs sintéticos; peso de muestra en entrenamiento |

**Clases:** No Tóxico (0), Lenguaje Ofensivo (1), Discurso de Odio (2), Amenazas/Violencia (3).

**Modelado:** `max_length=128`, semilla por defecto `42`, métrica principal **F1-macro**.

## Referencia de evaluación

- `test.csv`: **460** filas  
- F1-macro publicado en V3: **0.8499** (tolerancia recomendada ±0.01 entre hardware)  
- `val.csv` y `test.csv` son **byte a byte idénticos** a los de B2 (hashes cortos en metadata: `45aabe9744711d74`, `5d1284efcc7df20f`).

## SHA-256 de archivos versionados

| Archivo | SHA-256 |
|---------|---------|
| `train.csv` | `e755a91814ab4f3bf29bd3aaa38806bd7712fb4c45cf90b78612ffc4054b9453` |
| `val.csv` | `33d89bf3686c302e9f8896abe68f7d4fc2468690abcd5142c538e9934bb1a4c3` |
| `test.csv` | `3239eb4ca59720e1a7aaa574ad38bad53db18c54f5e1424b381f68d1d0b2f1d6` |
| `test_adversarial.csv` | `9b9e428105c66ece32b3935ea89ce5dbaafe80c6133fce694fa221fa8f830a46` |
| `lexicon_emojis.csv` | `8ab9bf7afbbb72929d2c1c42844e22814a85b3cce9691c053fa63a4a1553a732` |

## Reconstrucción del train

No está habilitada en `main` sin `data/raw/lexicon_salvadoreno.csv` (~2 035 variantes). Los sintéticos V3 ya están materializados en `train.csv` congelado.
