#!/bin/bash
# Levanta Caddy y MLflow en el servidor. Se corre con sudo desde la carpeta deploy/ del repo.
set -euo pipefail
cd "$(dirname "$0")"

AWS_REGION=us-east-1
ARTIFACTS_BUCKET=bolsa-lab-site-mlflow-artifacts

# El hash de la contraseña de MLflow vive cifrado en Parameter Store, nunca en git.
HASH=$(aws ssm get-parameter --region "$AWS_REGION" --name /bolsalab/mlflow_password_hash \
  --with-decryption --query Parameter.Value --output text)

# .env solo lo puede leer root; las comillas simples evitan que docker compose interprete los $ del hash.
umask 077
cat > .env <<EOF
AWS_REGION=$AWS_REGION
DOMAIN=bolsa-lab.site
ARTIFACTS_BUCKET=$ARTIFACTS_BUCKET
MLFLOW_USER=bolsalab
MLFLOW_PASSWORD_HASH='$HASH'
EOF

mkdir -p /opt/bolsalab/data/caddy /opt/bolsalab/data/mlflow /opt/bolsalab/data/site
aws s3 sync "s3://$ARTIFACTS_BUCKET/frontend/" /opt/bolsalab/data/site --delete --only-show-errors --region "$AWS_REGION"
docker compose up -d --build
# Caddy se recrea siempre para que lea el Caddyfile actual: si solo cambió ese archivo,
# compose no lo nota. Los certificados se conservan en /opt/bolsalab/data/caddy.
docker compose up -d --force-recreate --no-deps caddy
docker compose ps
