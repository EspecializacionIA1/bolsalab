# Servidor de MLflow con boto3 para guardar los artefactos en S3.
# Las versiones salen de requirements.txt (uv pip compile requirements.in).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /bin/uv
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt

EXPOSE 5000
