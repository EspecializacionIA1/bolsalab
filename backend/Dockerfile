# Imagen de la API. Se construye desde la raíz del repo:
#   docker build -f backend/Dockerfile -t bolsalab-api .
FROM python:3.12-slim

# XGBoost y LightGBM necesitan la librería OpenMP del sistema.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /bin/uv
COPY backend/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt

# Solo lo necesario para predecir: el paquete, el modelo congelado y la API.
WORKDIR /app
COPY bolsalab/ bolsalab/
COPY models/crash_reaction_v1.joblib models/crash_reaction_v1.json models/
COPY backend/app/ backend/app/

# Corre sin permisos de administrador.
RUN useradd --system --no-create-home api
USER api

EXPOSE 8000
# --proxy-headers: toma la IP real que manda Caddy, para el límite por IP.
# Aceptar los encabezados de cualquier origen es seguro porque el puerto 8000
# no se publica: solo Caddy llega a la API.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
