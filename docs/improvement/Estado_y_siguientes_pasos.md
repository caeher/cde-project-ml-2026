# Estado del proyecto y cómo retomarlo (15 de octubre de 2026, actualizado)

Documento para continuar en una **sesión nueva** (la anterior llegó al 89 % de contexto). Plan completo: `docs/improvement/Plan_mejora.md`. Historial y cifras: `CHANGELOG.md`.
**Restricción de la persona responsable: no usar «uso extra» de la cuenta.** Evitar lanzar agentes (Opus es lo más caro) mientras la ventana de 5 horas esté alta.

## Dónde estamos en el plan
| Fase | Estado |
|---|---|
| 0. Congelar y ordenar | **Hecha.** `src/data/build_dataset_final.py`, banco en `data/evaluation/frozen_bank/` con SHA-256 |
| 1. Datos con cuotas | **Hecha.** Odio 850 · Amenazas 559 · train 12,641 filas |
| 2. Hiperparámetros (Optuna) | **Hecha.** 0.6312 → 0.6486 (CV por hilo): `reports/improvement/optuna_cv_hilo.json` |
| 3. Candidatos A / B / C | **Hecha** (3 semillas c/u): `reports/improvement/fase3_candidatos.md`. Ganador: C como profesor |
| 4. Un solo modelo | **Hecha.** `models/v3.4.0` (418 MB), en la API. Media entre semillas: F1 0.717, Odio 0.626 |
| 5. Informe de sesgos | **Hecha.** `reports/improvement/fairness.md` (v3.4.0) y `fairness_v3.3.0.md` |
| 6. Prototipo + video | Panel nuevo, `scripts/arrancar_demo.ps1`, `docs/defense/Guion_Video_3min.md` listos. **Falta grabar el video** |
| 7. Documentos | Borrador `docs/defense/Impacto_social_y_politica.md` (rellenar `[[ ]]`). Faltan Etapa II actualizada, tesina, diapositivas, repo público |

## Modelo actual (banco congelado, n = 1,391)
`models/v3.4.0`: F1-macro 0.720 [0.687, 0.754] (v3.3.0: 0.693) · Odio 0.669 (media 3 semillas 0.626) · Amenazas 0.470 · FPR 0.112 · test oficial 0.832. **Metas no logradas:** Amenazas ≥ 0.60, y Odio ≥ 0.65 no es robusto entre semillas. **Hallazgo de sesgo:** FPR con jerga 0.379 vs 0.074 sin jerga (test oficial, n = 29 con jerga).
Rollback: `MODELOS` en `app/api/main.py` → `models/v3.3.0`.

## Para retomar
1. Si se quiere subir Amenazas: más datos de Amenazas y reentrenar (el cuello de botella son los datos, no los hiperparámetros); mitigar jerga con más No Tóxico con groserías afectivas.
2. Documentos (fase 7) con las cifras de `reports/improvement/fase3_candidatos.md` y `reports/improvement/fairness.md`.
3. Grabar el video siguiendo `docs/defense/Guion_Video_3min.md`.

## Cosas pendientes que dependen de la persona responsable
- Decidir si se sube la meta de F1-macro a ≥ 0.75 (la actual ≥ 0.70 ya casi se cumple).
- Revisar (opcional) las 125 etiquetas en `data/annotation/threads/review/revision_125.html`.
- Reconectar BrowserOS si se vuelven a recolectar hilos (tras cada reconexión, listar pestañas antes de abrir).
- Aplicar la fe de erratas al reporte de la Etapa II (está en el repo del equipo, rama v3).

## Trampas conocidas
- Ejecutar siempre con `.venv\Scripts\python.exe` (el Python del sistema no tiene `emoji`).
- No leer archivos de salida de agentes a medio escribir: esperar la notificación de fin de cada agente.
- Los agentes necesitan directorios temporales propios (`salida_*.csv` en `data/annotation/threads/blind/`).
- El equipo se suspende y mata procesos largos: usar estudios reanudables y comprobar `tasklist | grep python`.
