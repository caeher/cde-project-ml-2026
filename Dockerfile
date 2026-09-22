FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_CACHE_DIR=/opt/huggingface-cache \
    PRELOAD_MODELS=all \
    PRELOAD_DEFAULT=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código se copia sin la carpeta models/: los pesos siempre llegan desde
# Hugging Face en el paso de build de abajo.
COPY app ./app
COPY src ./src

ARG PRELOAD_MODELS=all
RUN PRELOAD_MODELS=${PRELOAD_MODELS} python -m app.api.download_models

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
