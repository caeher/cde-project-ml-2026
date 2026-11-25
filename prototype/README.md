# Prototipos de Julio

Material recuperado de `newprotypeV3`, commit
`a962019f7d54ca67a8b9fed9ad684deea71502b3`. Los datos, informes y artefactos
conservan su contenido original; se adaptaron los scripts y el notebook V4
para las rutas actuales. Sus datasets no se mezclan con `data/dataset/`.

## Contenido

- `ModeloV4.ipynb`: notebook previo al entrenamiento final con HatEval.
- `data/`: particiones históricas unificadas de Julio.
- `docs/`: fichas e informes V4 y v5.1, en Word y PDF, y documentación del
  prototipo que Julio trasladó desde `docs/` en su rama.
- `inferenciav2.py` y `prediccion3.py`: scripts de inferencia integrados con la API.
- `xlm_roberta_hate_speech_sv/`: configuración y tokenizador originales.

El entrenamiento final con HatEval ya se incorporó a `main` en `7e4329a`:

- [Notebook final](../notebooks/train/xlmr_hateval/ModeloFinal.ipynb).
- [Dataset fusionado](../data/external/hateval/train_merged_hateval.csv).
- [Instrucciones del entrenamiento final](../notebooks/train/xlmr_hateval/README.md).

Se mantienen esas rutas para evitar duplicar el notebook final y el CSV.

## Inferencia

Ambos scripts comparten el cargador `src/models/xlmr.py` con la API. Buscan un
modelo completo primero en `models/xlmr_hate_speech_sv/`, después en
`prototype/xlm_roberta_hate_speech_sv/` y `prototype/mi_modelo_xlmr/`.
Las carpetas que solo contienen configuración y tokenizador se omiten.
Si no hay pesos locales, usan la revisión publicada que ya estaba fijada en
la API. La primera carga remota necesita Internet y espacio para XLM-R large;
las dependencias se declaran en `requirements.txt`.

Se puede indicar otra carpeta mediante `XLMR_MODEL_PATH` (las rutas relativas
se resuelven desde la raíz del repositorio). Una ruta explícita incompleta
produce un error descriptivo. Ya no hay rutas personales ni inferencia al
importar `prediccion3.py`. La normalización y el orden de clases coinciden con
los utilizados por la API.

El `config.json` histórico describe XLM-R **base** (12 capas, dimensión 768).
No debe copiarse sobre la configuración del XLM-R **large** del entrenamiento
final o de la API. Para la aplicación vigente, utilizar el catálogo existente
de la API (`xlmr_hf` o `xlmr_local`) y sus rutas documentadas en el proyecto.

## Notebook V4

Abrir `ModeloV4.ipynb` dentro del repositorio, desde la raíz o desde
`prototype/`. Usa las tres particiones ya versionadas en `prototype/data/`,
sin solicitar archivos por Colab ni reconstruir el dataset vigente. Los
checkpoints se escriben en `runs/xlmr_base_v4/` y el modelo base entrenado en
`prototype/xlm_roberta_hate_speech_sv/`. La evaluación adversarial consulta
`data/dataset/test_adversarial.csv`.

La regla global `*.safetensors` de `.gitignore` ya cubre los pesos que Julio
excluyó específicamente; no se necesita modificarla.

Consulta la [revisión de integración](../docs/improvement/Revision_Julio_newprotypeV3.md)
para ver la comparación por commit y el alcance.
