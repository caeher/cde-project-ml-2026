# Dataset v2.0.0 y candidato v3.6.0: evaluación con hilos apartados (6 de noviembre de 2026)

Autorizado por la persona responsable tras ver que val (459) y test (460) son solo de la Etapa I y demasiado pequeños para el train actual (20 mil filas, 75 % hilos de X). Criterios fijados **antes** de entrenar.

## Partición (src/data/particion_v2.py, semilla 2026)
- 18 hilos completos de la ronda 3 fuera del entrenamiento: 3 por grupo (A amenazas, B fútbol/humor, C política) a `val_hilos` y 3 por grupo a `test_hilos`, elegidos entre 20,000 asignaciones al azar por cercanía a la distribución de clases, con mínimos de 120 Amenazas, 25 Odio y 300 Ofensivo por mitad.
- 30 % de las búsquedas de jerga (tuits independientes), mitad a cada conjunto.
- Solo textos con consenso A = B. `val_hilos` 2,314 (NT 1,559 · OF 594 · OD 29 · AM 132); `test_hilos` 1,975 (NT 1,307 · OF 514 · OD 28 · AM 126).
- val, test, batería y banco congelado sin cambios (mismos SHA-256).

## Conjuntos
- **Selección** (early stopping, semilla del estudiante, temperatura): `val_v2` = val oficial (459) + val_hilos (2,314) = 2,773.
- **Test principal**: `test_hilos` (1,975) + banco congelado (1,391) = 3,366 (Odio 158 · Amenazas 243). Nunca se usa para elegir.
- Se reportan aparte: banco solo, test_hilos solo, test oficial, sonda afectiva, FPR sobre No Tóxico de jerga (búsquedas reservadas de test_hilos).
- Comparables en el test principal: solo modelos que no vieron esos hilos (v3.0.0–v3.4.0 y los entrenados con v2.0.0). Los entrenados con v1.9.0 (Profesor R3, v3.5.0-rc1, mBERT-SV) vieron test_hilos: se reportan solo en el banco.

## Entrenamiento (sin variantes a mitad de camino)
Misma receta que la ronda 3: receta B (Optuna) × 3 semillas como profesor (`candB_v2`) → temperatura en val_v2 → destilación T 1, α 0.5, 3 semillas (`v3.6.0-rc1`) → semilla por F1 en val_v2.

## Criterios de adopción frente a v3.4.0 (test principal, una sola medición)
1. F1-macro: mejora pareada con IC 95 % > 0.
2. Falsos positivos: FPR sobre No Tóxico no sube más de 0.01.
3. Recall de Amenazas ≥ 0.55.
4. Recall de Odio no baja más de 0.03.
5. Sonda afectiva ≥ 17/20 y ≥ 16/18.
6. Test oficial ≥ 0.82.
7. FPR sobre No Tóxico de jerga (test_hilos) menor que el de v3.4.0.
Se evalúan el estudiante (v3.6.0-rc1) y el profesor (candB_v2). Si ninguno cumple los 7, v3.4.0 sigue en la API y se documenta.
