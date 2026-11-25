# Prototipos de Julio

Material recuperado de `newprotypeV3`, commit
`a962019f7d54ca67a8b9fed9ad684deea71502b3`. Los 21 archivos importados
conservan exactamente sus bytes originales. Esta carpeta es independiente de
la API y del pipeline vigente; sus datasets no se mezclan con `data/dataset/`.

## Contenido

- `ModeloV4.ipynb`: notebook previo al entrenamiento final con HatEval.
- `data/`: particiones históricas unificadas de Julio.
- `docs/`: fichas e informes V4 y v5.1, en Word y PDF, y documentación del
  prototipo que Julio trasladó desde `docs/` en su rama.
- `inferenciav2.py` y `prediccion3.py`: scripts originales de inferencia local.
- `xlm_roberta_hate_speech_sv/`: configuración y tokenizador originales.

El entrenamiento final con HatEval ya se incorporó a `main` en `7e4329a`:

- [Notebook final](../notebooks/train/xlmr_hateval/ModeloFinal.ipynb).
- [Dataset fusionado](../data/external/hateval/train_merged_hateval.csv).
- [Instrucciones del entrenamiento final](../notebooks/train/xlmr_hateval/README.md).

Se mantienen esas rutas para evitar duplicar el notebook final y el CSV.

## Uso de los scripts históricos

Los pesos entrenados no están incluidos en la rama de origen. La configuración
y el tokenizador por sí solos no permiten ejecutar inferencia.
`inferenciav2.py` busca pesos junto al script, en
`xlm_roberta_hate_speech_sv/` o `mi_modelo_xlmr/`. `prediccion3.py` conserva una
ruta absoluta del equipo de Julio y carga el modelo al ejecutarse o importarse;
requiere adaptar esa ruta en una copia local antes de usarlo.

El `config.json` histórico describe XLM-R **base** (12 capas, dimensión 768).
No debe copiarse sobre la configuración del XLM-R **large** del entrenamiento
final o de la API. Para la aplicación vigente, utilizar el catálogo existente
de la API (`xlmr_hf` o `xlmr_local`) y sus rutas documentadas en el proyecto.

La regla global `*.safetensors` de `.gitignore` ya cubre los pesos que Julio
excluyó específicamente; no se necesita modificarla.

Consulta la [revisión de integración](../docs/improvement/Revision_Julio_newprotypeV3.md)
para ver la comparación por commit y el alcance.
