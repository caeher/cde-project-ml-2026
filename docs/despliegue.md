# Despliegue de app/

URL: https://cdeml.server.caeher.com

- Interfaz: `app/ui/app.py`, Streamlit en `127.0.0.1:8511`.
- API privada: `app/api/main.py`, FastAPI en `127.0.0.1:8011`.
- Servicios: `cdeml-ui.service` y `cdeml-api.service`, habilitados al arrancar.
- Nginx: `/etc/nginx/sites-available/cdeml`.
- HTTPS: certificado Let's Encrypt con renovación automática por Certbot.
- Runtime reutilizado: `/root/cde-project-ml-2026/.venv`. No eliminar ese entorno mientras estos servicios lo utilicen.
- Argilla y la aplicación anterior no se modifican.

## Modelos

`scripts/download_deploy_models.py` descarga revisiones fijas de RoBERTuito
v3.6.0 y mBERT `caeher/mbert-toxicidad-sv-v2` a `models/`, y XLM-R Large a la caché de Hugging Face.
RoBERTuito usa la temperatura de `inference_contract.json` (1.415).
mBERT promedia las probabilidades de las semillas 42, 1337 y 2026, sin recalibrarlas.
v3.6.0 es el modelo predeterminado. Solo se mantiene un modelo en memoria;
las peticiones de inferencia se serializan para evitar cargas concurrentes.
Cambiar de modelo implica volver a cargar sus pesos desde disco.

## Operación

```bash
systemctl status cdeml-api cdeml-ui
journalctl -u cdeml-api -u cdeml-ui -n 100 --no-pager
systemctl restart cdeml-api cdeml-ui
curl -f https://cdeml.server.caeher.com/_stcore/health
curl -f http://127.0.0.1:8011/modelos
```

La interfaz usa `API_URL=http://127.0.0.1:8011`, definida en su servicio.
La API no se publica directamente en Internet.
