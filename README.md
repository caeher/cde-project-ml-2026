# Análisis del Discurso de Odio en Redes Sociales en El Salvador

Proyecto de Machine Learning para detectar, clasificar y analizar discurso de odio en contenido de redes sociales del contexto salvadoreño.

## Estructura del proyecto

```
├── config/              # Configuración (YAML)
├── data/
│   ├── raw/             # Datos sin procesar (tweets, comentarios, etc.)
│   ├── interim/         # Datos en transformación intermedia
│   ├── processed/       # Datasets listos para modelado
│   └── external/        # Fuentes externas (lexicones, listas de palabras)
├── docs/                # Documentación del proyecto
├── models/
│   └── checkpoints/     # Modelos entrenados (.joblib, etc.)
├── notebooks/           # Jupyter notebooks de exploración
├── reports/
│   └── figures/         # Gráficos y reportes visuales
├── scripts/             # Scripts ejecutables (CLI)
├── src/
│   └── discurso_odio/   # Código fuente del paquete
│       ├── data/        # Carga de datos
│       ├── features/    # Preprocesamiento y features
│       ├── models/      # Entrenamiento e inferencia
│       └── utils/       # Utilidades (rutas, helpers)
└── tests/               # Pruebas unitarias
```

## Requisitos

- Python 3.10 o superior
- pip

## Configuración del entorno

### 1. Crear y activar el entorno virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3. Variables de entorno (opcional)

```bash
cp .env.example .env
```

## Uso rápido

```bash
# Verificar configuración y rutas de datos
python scripts/prepare_data.py

# Preparar pipeline de entrenamiento
python scripts/train_model.py

# Ejecutar pruebas
pytest
```

## Flujo de trabajo sugerido

1. **Recolección** — Guardar datos crudos en `data/raw/`
2. **Preprocesamiento** — Limpiar y etiquetar en `data/interim/` y `data/processed/`
3. **Exploración** — Notebooks en `notebooks/`
4. **Modelado** — Entrenar con `src/discurso_odio/models/`
5. **Evaluación** — Métricas y figuras en `reports/figures/`

## Configuración

Edita `config/settings.yaml` para ajustar rutas, columnas del dataset y parámetros del modelo.

## Licencia

MIT — ver [LICENSE](LICENSE).
