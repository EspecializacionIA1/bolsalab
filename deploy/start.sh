#!/bin/bash
# Levanta Caddy y MLflow en el servidor. Se corre con sudo desde la carpeta deploy/ del repo.
set -euo pipefail
cd "$(dirname "$0")"

AWS_REGION=us-east-1

# El hash de la contraseña de MLflow vive cifrado en Parameter Store, nunca en git.
HASH=$(aws ssm get-parameter --region "$AWS_REGION" --name /bolsalab/mlflow_password_hash \
  --with-decryption --query Parameter.Value --output text)

# .env solo lo puede leer root; las comillas simples evitan que docker compose interprete los $ del hash.
umask 077
cat > .env <<EOF
AWS_REGION=$AWS_REGION
DOMAIN=bolsa-lab.site
ARTIFACTS_BUCKET=bolsa-lab-site-mlflow-artifacts
MLFLOW_USER=bolsalab
MLFLOW_PASSWORD_HASH='$HASH'
EOF

mkdir -p /opt/bolsalab/data/caddy /opt/bolsalab/data/mlflow
docker compose up -d --build
docker compose ps
