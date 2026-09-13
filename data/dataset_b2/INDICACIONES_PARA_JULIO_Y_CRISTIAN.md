# Indicaciones — Reentrenamiento con el dataset B2

**Para:** Julio (XLM-RoBERTa) y Cristian (mBERT)
**De:** Willian
**Fecha:** 14 de agosto de 2026

---

## Lo que les estoy pasando

La carpeta `data/dataset_b2/` con el dataset corregido y ampliado, más un conjunto de pruebas para verificar que los modelos quedaron bien **antes** de devolvérmelo.

| Archivo | Qué es |
|---|---|
| `train.csv` | 3,293 filas para entrenar |
| `val.csv` | 459 filas — **idéntico al v1** |
| `test.csv` | 460 filas — **idéntico al v1** |
| `test_adversarial.csv` | 144 pruebas de robustez |
| `lexicon_emojis.csv` | Catálogo de emojis reconstruido |
| `metadata.json` | Pesos de clase y configuración |
| `README.md` | Detalle de qué cambió y por qué |

---

## Las 4 clases — no hay más

Todo el proyecto usa **exactamente cuatro clases**. Cualquier resultado que salga de un modelo tiene que ser una de estas:

| label | resultado_esperado |
|---|---|
| 0 | No Tóxico |
| 1 | Lenguaje Ofensivo |
| 2 | Discurso de Odio |
| 3 | Amenazas/Violencia |

En `test_adversarial.csv` la columna **`resultado_esperado`** trae el nombre de la clase que el modelo debería devolver en cada caso, y **`label_esperado`** el número equivalente para comparar en código.

> Las letras A, B, C… G de la columna `grupo_de_prueba` **no son clases**. Son el tipo de prueba que se está haciendo (ofuscación, emojis, jerga, etc.).

---

## Paso 1 — Entrenar

Usen `data/dataset_b2/` y **los pesos de clase nuevos**. Los del v1 ya no sirven porque la distribución de train cambió.

```python
pesos = [0.9198, 0.9376, 0.9720, 1.2233]   # No Tóxico, Ofensivo, Odio, Amenazas
loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(pesos, dtype=torch.float))
```

Todo lo demás igual que antes: `max_length=128`, `batch_size=16`, `lr=2e-5`, semilla 42, `texto_modelo` como campo de entrada.

**Importante:** los dos tienen que entrenar con este mismo dataset y estos mismos pesos. Si uno usa B2 y el otro el v1, la comparación entre modelos no vale nada.

---

## Paso 2 — Evaluar sobre `test.csv`

Como `test.csv` no cambió, el F1 es **directamente comparable** con lo que ya reportaron:

| Modelo | F1-macro con v1 | Con B2 |
|---|---|---|
| XLM-R | 0.8058 | ¿? |
| mBERT | 0.7862 | ¿? |

Si baja mucho, avisen antes de seguir: puede indicar que algo se configuró distinto.

---

## Paso 3 — Correr `test_adversarial.csv`

Este es el paso que les pido que **no se salten**. Son 144 casos donde ya sabemos cuál debería ser la respuesta.

```python
adv = pd.read_csv("data/dataset_b2/test_adversarial.csv")
adv["prediccion"] = modelo.predict(adv["texto_normalizado"])   # 0..3
adv["correcto"] = adv["prediccion"] == adv["label_esperado"]

# Resumen por tipo de prueba
print(adv.groupby("grupo_de_prueba")["correcto"].agg(["sum", "size"]))
```

### Marcas a superar — resultados del XLM-R entrenado con el v1

| Grupo de prueba | Casos | Acierto v1 |
|---|---|---|
| A. Ofuscación de groserías | 20 | 85% |
| B. Emojis | 18 | 33% |
| C. Amenazas ofuscadas | 11 | 45% |
| D. Jerga salvadoreña inofensiva | 14 | 57% |
| E. Control sin jerga | 12 | 100% |
| F. Falsos amigos dialectales | 34 | 41% |
| G. Pares mínimos de emoji | 35 | 34% |
| **Global** | **144** | **~50%** |

**Lo que esperamos que suba:** B, C, F y G. Son los cuatro huecos que el B2 corrige con datos nuevos.

**Lo que no debería bajar:** A y E. Si bajan, algo se rompió.

---

## Paso 4 — Revisar los casos que fallan

No basta con el porcentaje. Revisen a mano los que salgan mal, sobre todo estos:

**Jerga salvadoreña que debe salir No Tóxico:**

- «Ese maje es bien pajero, nunca cumple» — *pajero* = mentiroso
- «El chucho de la vecina ladra toda la noche» — *chucho* = perro
- «Prestame pisto para el pasaje porfa» — *pisto* = dinero
- «Está bien vergón el carro que te compraste» — *vergón* = excelente
- «Había un cachimbo de gente en el mercado» — *cachimbo* = mucho

**Emojis que deben cambiar la clase:**

- «Ya sabés lo que te espera 🎂» → No Tóxico
- «Ya sabés lo que te espera 🔫» → Amenazas/Violencia
- «Te voy a buscar mañana ❤️» → No Tóxico
- «Te voy a buscar mañana 🔪» → Amenazas/Violencia
- «Los que vienen del sur ⚽» → No Tóxico
- «Los que vienen del sur 🐒» → Discurso de Odio

Si un `❤️` o un `🎂` siguen empujando el texto a Ofensivo, el problema del emoji **no se corrigió** y hay que avisar antes de seguir.

---

## Paso 5 — Exportar predicciones

Esto es indispensable para la comparativa estadística entre los dos modelos. **Dos columnas, nada más:**

```python
test = pd.read_csv("data/dataset_b2/test.csv")
test["y_pred"] = mis_predicciones          # enteros 0..3, en el mismo orden
test[["ID", "y_pred"]].to_csv("reports/preds_xlmr_b2.csv", index=False)
#                                          preds_mbert_b2.csv para Cristian
```

Sin este archivo no se puede hacer la prueba de McNemar y la comparación se queda en «un número contra otro», que no demuestra nada.

---

## Qué me devuelven

1. El modelo entrenado, **con los pesos** (Cristian: los del v1 nunca llegaron).
2. `preds_*_b2.csv` con las dos columnas.
3. `test.csv` evaluado: F1-macro, F1 por clase y matriz de confusión.
4. `test_adversarial.csv` evaluado: tabla por grupo de prueba.
5. Una nota corta con los casos que siguen fallando y su opinión de por qué.

---

## Antes de mandármelo, revisen

- [ ] Entrené con `data/dataset_b2/`, no con el v1
- [ ] Usé los pesos de clase nuevos
- [ ] El modelo solo devuelve valores 0, 1, 2 o 3
- [ ] `max_length = 128` tanto en entrenamiento como en inferencia
- [ ] Apliqué la misma normalización (`texto_normalizado` ya viene lista)
- [ ] Corrí `test.csv` **y** `test_adversarial.csv`
- [ ] Exporté `preds_*_b2.csv` con las columnas `ID,y_pred`
- [ ] Revisé a mano los casos de jerga y de emoji del paso 4

---

## Correcciones pendientes de la auditoría

Aparte del reentrenamiento, quedan estas de la revisión anterior:

**Julio:**
- Recalcular el FPR por jerga — quitar el `fpr_values = [0.142, 0.385]` escrito a mano. Los reales son 15.96% y 44.83%
- Corregir `Presencia_Sar` → `Presencia_Sarcasmo` y `Presencia_Iro` → `Presencia_Ironia`, y comparar contra `"SI"`/`"SÍ"`, no contra `1`
- En §3.1 los valores por plataforma son 0.867 y 0.715, no 0.85 y 0.69

**Cristian:**
- `trivial_baselines`: la clase mayoritaria da **0.128**, no 0.087
- Que el pipeline guarde las predicciones en cada corrida
