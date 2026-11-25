# Revisión de los cambios de Julio en newprotypeV3

Fecha: 25 de noviembre de 2026. Referencias actualizadas con `git fetch origin --prune`.

## Integración funcional posterior

Por solicitud del usuario, se preparó la incorporación a `main` junto con
correcciones de integración. El registro de importación inicial que sigue
describe el commit `df908c1`; las afirmaciones sobre archivos idénticos y pruebas
corresponden exclusivamente a esa primera importación.

En esta segunda fase se realizó únicamente revisión y edición estática. No se
ejecutaron pruebas, notebooks, aplicación, entrenamiento ni inferencia, ni se
instalaron dependencias o descargaron pesos.

- La API y ambos scripts utilizan el mismo cargador, revisión remota, validación
  de etiquetas y normalización. Se eliminó la ruta personal de `prediccion3.py`
  y se movió su inferencia al punto de entrada protegido por `__main__`.
- El cargador omite carpetas sin pesos, reconoce pesos únicos o fragmentados y
  admite `XLMR_MODEL_PATH`. Sin pesos locales utiliza el modelo publicado fijado
  previamente en la API; una ruta explícita incompleta produce un error claro.
- Si faltan los pesos de RoBERTuito y no se configuró `API_MODELO_DEFAULT`, la
  API selecciona XLM-R local completo o, en su defecto, XLM-R publicado. Se
  respeta cualquier selección explícita del usuario.
- El notebook V4 lee sus particiones versionadas sin depender de Colab y
  guarda sus pesos base en su propia carpeta. El notebook final guarda los
  pesos large en la ruta que usa la API; su evaluación final resuelve las rutas
  actuales de val/test. La documentación identifica su celda de entrada.
- Los CSV, documentos y JSON históricos se conservan; el dataset vigente no se
  modifica. No se cambia la lista de dependencias.

El funcionamiento en ejecución depende de las dependencias instaladas, los
pesos locales o el acceso al modelo publicado y la memoria disponible. La
revisión estática no sustituye una comprobación en ejecución.

## Registro de la importación inicial

- Origen revisado: `newprotypeV3` / `origin/newprotypeV3`,
  `a962019f7d54ca67a8b9fed9ad684deea71502b3`.
- Base revisada: `main` / `origin/main`,
  `3a09657eea1a7d9de6c0472a0ec7b3070fc5fc24`.
- Rama de integración local: `integration/julio-newprotypeV3`, basada en esa
  revisión de `origin/main`.

## Resultado de la comparación

La integración previa era parcial. Los seis commits con autor `JulioMata`
exclusivos de la rama de origen no son ancestros de `main`, pero parte de su
contenido se incorporó mediante `7e4329a` y la API multi-backend de `6d8642a`.
El archivo `_integration_shas.txt` registra la revisión de origen; esa referencia
no implica que se hayan importado todos sus archivos.

| Commit de Julio | Aporte | Estado en la base main | Resolución en esta rama |
|---|---|---|---|
| `9015d39` | Tres particiones `*_unificado.csv` | Sin copia idéntica en el árbol | Añadidas en `prototype/data/` |
| `91391b4` | `ModeloV4.ipynb` | Sin copia idéntica | Añadido en `prototype/` |
| `ae0be9e` | Dos scripts de inferencia local | Sin copia idéntica; la API ya tiene su propia inferencia XLM-R | Añadidos como scripts históricos en `prototype/` |
| `3fa3337` | Configuración y tokenizador; exclusión de pesos | Sin copia idéntica de los tres JSON; `*.safetensors` ya cubre la exclusión | Añadidos en `prototype/xlm_roberta_hate_speech_sv/` |
| `b3f5606` | Notebook final y corpus fusionado HatEval | Ya incorporados mediante `7e4329a` en otras rutas | Se conservan las rutas existentes |
| `a962019` | Ocho informes/fichas Word/PDF y traslado de documentación | Sin copias idénticas de esos documentos | Añadidos en `prototype/docs/`, sin mover la documentación vigente |

El CSV `prototype/newdata/train_merged_hateval.csv` coincide byte por byte con
`data/external/hateval/train_merged_hateval.csv` de `main` (mismo blob Git).
El notebook final mantiene las 61 celdas: solo difiere el código de las celdas
56 y 57 (índices desde cero), donde la integración previa adaptó las rutas de
salida del CSV y las rutas de train/val/test a la estructura de `main`.

## Integración aditiva

Se recuperan 21 archivos originales bajo `prototype/`: un notebook, tres CSV,
dos scripts, tres JSON, ocho documentos Word/PDF, tres Markdown y un `.gitkeep`.
Se añaden este informe y `prototype/README.md` para explicar su procedencia y
sus limitaciones. Los archivos originales se copian sin editar su contenido.

No se fusiona la rama completa: contiene una estructura antigua distinta de la
actual. La importación seleccionada permite conservar el árbol vigente, la API,
su modelo predeterminado `v3.6.0`, las dependencias y los datasets de evaluación.
Los tres datasets recuperados son material histórico independiente; no se
declara que sean compatibles con las particiones actuales ni se usan para
entrenamiento o evaluación en esta integración.

Los pesos no se encuentran en los archivos versionados del origen. Los scripts
locales requieren esos pesos; `prediccion3.py` también contiene una ruta absoluta
del equipo de Julio. El `config.json` recuperado es de XLM-R base, distinto del
XLM-R large final: se conserva junto al prototipo y no se instala en `models/`.

## Verificación

- Comparación de los blobs Git del origen y `main`, incluyendo rutas distintas.
- Comparación de todas las celdas y fuentes del notebook final en ambas ramas.
- Comprobación byte por byte de los 21 archivos recuperados contra el origen.
- Comprobación de que todos los archivos versionados de la base conservan su
  contenido y de que la integración solo añade archivos.
- Validación de sintaxis de los dos scripts, estructura JSON de los artefactos
  y del notebook V4, y lectura de los tres CSV.
- Ejecución de las pruebas rápidas existentes de `tests/test_estructura.py`.

Resultados: las comprobaciones de integridad, sintaxis y formato pasaron. Los
CSV recuperados contienen 26,840 filas de train, 5,751 de val y 5,752 de test,
con 37 columnas. De las nueve pruebas existentes, cuatro pasaron y cinco
terminaron con errores de importación porque el Python local no tiene
`pandas`, `scipy` ni `emoji`. No se modificó el entorno para esta importación
documental e histórica. La coincidencia con `main` de los archivos existentes
se verifica mediante Git, que normaliza los finales de línea de Windows.
La revisión del índice confirma 23 altas, ninguna modificación y ninguna baja;
los 21 blobs importados coinciden con el origen. `git diff --check` detecta
espacios finales heredados en los CSV, `etapa1.md` y `prediccion3.py`; se
conservan para mantener íntegros los datos y originales de Julio. Los dos
archivos nuevos de documentación no presentan errores de espacios.

No se ejecutan notebooks, entrenamiento ni inferencia con modelos: los pesos
del prototipo no vienen incluidos. Esta revisión prepara una integración local;
no publica cambios ni modifica la referencia remota `main`.
