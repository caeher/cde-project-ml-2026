# Ronda 3: Amenazas implícitas y jerga salvadoreña (29 de octubre de 2026)

Ronda adicional a las dos de la fase 1, autorizada por la persona responsable tras ver v3.4.0. Criterios fijados **antes** de recolectar y entrenar.

## Diagnóstico de v3.4.0 (banco congelado, solo lectura)
- **Amenazas:** 62 de 117 no detectadas; 41 se predicen No Tóxico con p(AM) media 0.08 (las acertadas: 0.93). No son errores de umbral: bajar el umbral a 0.1 solo llega a recall 0.60 subiendo los falsos positivos. Son **celebraciones o apologías implícitas de violencia** que la guía v2.0 (§3.3) etiqueta como Amenazas: «merecen eso y más», «eso son caricias», «excelente terapia educativa», «el que a hierro mata…», «la cárcel es poco castigo». El entrenamiento tiene sobre todo amenazas explícitas, ofuscadas o con emoji.
- **Jerga:** en train hay 226 textos No Tóxico con jerga, pero solo **22 reales** (17 de la Etapa I + 5 de hilos); el resto es sintético. Los hilos recolectados son hostiles, así que el modelo aprende «jerga ⇒ tóxico» (FPR con jerga 0.38 frente a 0.07 sin jerga en el test oficial).

## Datos a recolectar (BrowserOS, respuestas públicas, sin usuarios)
| Objetivo | Hilos | Cuota con consenso |
|---|---|---|
| Amenazas por celebración/apología implícita | capturas y traslados de pandilleros, CECOT, régimen de excepción, linchamientos, delincuentes abatidos (El Salvador y región) | ≥ 300 Amenazas nuevas |
| No Tóxico con jerga salvadoreña real | fútbol (Selecta, Alianza, FAS, Águila), humor y memes salvadoreños, comida, fiestas, conversación casual | ≥ 300 No Tóxico con jerga; también se guardan los Ofensivos con jerga (evita el atajo inverso «jerga ⇒ No Tóxico») |
Reserva: **2 hilos de jerga completos** quedan fuera del entrenamiento como `jerga_dev` para elegir la variante (no es el banco congelado).

## Etiquetado
Dos anotadores a ciegas con **Haiku 5.5** (instrucción de la persona responsable) con la guía v2.0 y, para reducir errores correlacionados, con instrucciones distintas (uno lee la guía completa, otro un resumen con los casos límite de §3.3 y §5); los desacuerdos los adjudica Claude (modelo principal) con la guía. Se reporta κ. Limitación declarada: anotadores del mismo modelo.

## Entrenamiento (sin variantes nuevas a mitad de camino)
- Dataset **v1.9.0** = v1.8.0 + ronda 3 (menos `jerga_dev`), con `build_dataset_final.py` (mismas comprobaciones de fuga).
- Receta B (Optuna) en 3 semillas como profesor → destilación con la configuración de v3.4.0 (T 1, α 0.5) → candidato **v3.5.0**.
- Selección entre semillas del estudiante: F1 de validación oficial (igual que v3.4.0).

## Criterios de adopción de v3.5.0 frente a v3.4.0 (una sola medición final)
1. **Amenazas:** recall en el banco congelado ≥ 0.55 (v3.4.0: 0.47) y mejora pareada con IC 95 % > 0 en F1 de Amenazas.
2. **Jerga:** FPR sobre No Tóxico con jerga en el test oficial ≤ 0.24 (nivel de v3.3.0; v3.4.0: 0.38), y en `jerga_dev` menor que v3.4.0.
3. **Sin regresiones:** F1-macro del banco no baja más de 0.01; test oficial ≥ 0.83; FPR global ≤ 0.12; sonda afectiva ≥ 17/20 y ≥ 16/18; recall de Odio no baja más de 0.03.
Si no se cumplen, v3.4.0 sigue en la API y el resultado se documenta como límite.
