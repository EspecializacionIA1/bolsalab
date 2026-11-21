# Infraestructura en AWS

BolsaLAB corre en un solo servidor de AWS (`us-east-1`), con el dominio `bolsa-lab.site`. Toda la infraestructura está escrita en Terraform (`infra/`) y lo que corre en el servidor, en `deploy/`.

| Dirección | Qué es | Acceso |
|---|---|---|
| https://bolsa-lab.site | La app. Por ahora, una página temporal | Pública |
| https://bolsa-lab.site/api/docs | La API en FastAPI y su documentación | Pública, con límite de 30 predicciones por minuto por IP |
| https://mlflow.bolsa-lab.site | Experimentos y modelo registrado | Usuario y contraseña del equipo |

## Cómo está armado

```
Navegador ──443──▶ EC2 t3.small ──▶ Caddy ──┬─▶ /api/* ──▶ API (FastAPI + modelo crash_reaction_v1)
                                             ├─▶ página estática (luego el frontend)
                                             └─▶ MLflow ──┬─ corridas: SQLite en el disco
                                                          └─ modelos: S3
```

- **Caddy** recibe todo el tráfico, saca y renueva solo los certificados HTTPS (Let's Encrypt) y pide la contraseña antes de dejar pasar a MLflow.
- **La API y MLflow** no tienen puertos abiertos: solo se llega a ellos a través de Caddy. Caddy le pasa a la API la IP real de cada usuario, para el límite por IP, y corta cualquier petición de más de 10 KB.
- **Sin SSH:** el servidor solo abre 80 y 443. Se entra con SSM Session Manager.
- **Sin claves guardadas:** el servidor usa un rol de IAM y nosotros entramos a AWS con IAM Identity Center (SSO).

## Terraform (`infra/`)

| Carpeta | Qué crea | Dónde guarda su estado |
|---|---|---|
| `infra/bootstrap/` | El bucket S3 donde Terraform guarda su estado (con versiones, cifrado y sin acceso público). Se aplica una sola vez | Local, no va a git |
| `infra/main/` | Red, servidor, IP fija, permisos, bucket de artefactos de MLflow, presupuesto de USD 25 y DNS en Route 53 | En el bucket de `bootstrap`, con bloqueo |

| Archivo de `infra/main/` | Qué tiene |
|---|---|
| `network.tf` | VPC propia con una subred pública. La cuenta no tenía VPC por defecto |
| `server.tf` | EC2 `t3.small` con Amazon Linux 2023, disco cifrado de 20 GB, CPU en modo `standard` (si se pasa, se vuelve lento pero no cobra más), solo IMDSv2 y una IP fija |
| `user_data.sh` | Al primer arranque instala Docker y docker compose, y crea 2 GB de swap |
| `iam.tf` | Rol del servidor: SSM, el bucket de artefactos y solo los parámetros `/bolsalab/*` |
| `storage.tf` | Bucket privado y cifrado para los artefactos de MLflow |
| `budget.tf` | Aviso por correo al 80 % del gasto real y si el pronóstico pasa los USD 25 |
| `dns.tf` | Zona de `bolsa-lab.site`: `A` para la raíz y para `mlflow`, `CNAME` de `www`, `CAA` (solo Let's Encrypt) y SPF y DMARC, que rechazan correos falsos con nuestro dominio |

El dominio está comprado en GoDaddy; allá solo cambiamos los servidores DNS por los de Route 53 (`terraform output name_servers`).

## Lo que corre en el servidor (`deploy/`)

| Archivo | Para qué |
|---|---|
| `docker-compose.yml` | Los servicios `caddy`, `api` y `mlflow`. La imagen de la API se construye con `backend/Dockerfile` |
| `Caddyfile` | Qué dominio va a dónde y dónde se pide la contraseña |
| `mlflow/Dockerfile` | MLflow 3.18 con boto3, instalado con uv |
| `mlflow/requirements.txt` | Versiones exactas, generadas con `uv pip compile requirements.in` |
| `site/index.html` | La página temporal |
| `start.sh` | Lee el hash de la contraseña de Parameter Store, crea el `.env` del servidor y levanta todo |

En el servidor, el repo vive en `/opt/bolsalab/repo` y los datos en `/opt/bolsalab/data` (certificados y base de MLflow), fuera de los contenedores.

## Usuario y contraseña de MLflow

- Usuario: `bolsalab`. La contraseña se comparte por un canal privado, nunca por git.
- En AWS solo guardamos su **hash** (bcrypt), cifrado en Parameter Store: `/bolsalab/mlflow_password_hash`.
- En el navegador aparece la ventana de inicio de sesión del propio navegador.
- Para usarlo desde código, en el `.env` local:
  ```
  MLFLOW_TRACKING_URI=https://mlflow.bolsa-lab.site
  MLFLOW_TRACKING_USERNAME=bolsalab
  MLFLOW_TRACKING_PASSWORD=...
  ```
  Sin esas líneas, el código vuelve a usar el `mlflow.db` local.

**Cambiar la contraseña:**
```powershell
docker run --rm -it caddy:2.10-alpine caddy hash-password
aws ssm put-parameter --name /bolsalab/mlflow_password_hash --type SecureString --overwrite --value '<hash>'
```
Y luego, en el servidor: `sudo bash /opt/bolsalab/repo/deploy/start.sh`.

## Tareas comunes

**Entrar a AWS desde la terminal:**
```powershell
$env:AWS_PROFILE = "bolsalab"
aws sso login
```

**Cambiar la infraestructura:**
```powershell
cd infra/main
terraform plan     # revisar que no diga "destroy" sin querer
terraform apply
```
Los cambios se hacen en el código, no con clics en la consola. Si se cambia algo a mano, Terraform lo revierte en el siguiente `apply`.

**Entrar al servidor** (necesita el *Session Manager plugin* de la CLI):
```powershell
cd infra/main
terraform output -raw connect_command
```

**Actualizar lo que corre en el servidor:**
```bash
cd /opt/bolsalab/repo/deploy
sudo git pull && sudo bash start.sh
sudo docker compose ps
sudo docker compose logs mlflow --tail 30
```

**Publicar las corridas y el modelo en MLflow** (no reentrena ni toca el 20 % de prueba), con el `.env` apuntando al servidor:
```bash
uv run python -m bolsalab.modeling.mlflow_backfill
uv run python -m bolsalab.modeling.mlflow_tracking
```

## Costo y cierre

Unos USD 18 entre el 21 de noviembre y el 15 de diciembre de 2026: el servidor, la IP fija, el disco y Route 53. Al terminar el proyecto:

```powershell
cd infra/main
terraform destroy
```

Borra todo menos el bucket del estado, que cuesta centavos. Si después se vuelve a crear, la zona de Route 53 trae servidores DNS nuevos y hay que cambiarlos otra vez en GoDaddy.

## Problemas que encontramos

| Síntoma | Causa | Arreglo |
|---|---|---|
| `terraform plan`: *no matching EC2 VPC found* | La cuenta no tenía VPC por defecto en `us-east-1` | Creamos una VPC propia (`network.tf`) |
| `aws configure sso`: *invalid_scope* | Valor equivocado en *SSO registration scopes* | Usar `sso:account:access` |
| MLflow abre, pero las corridas dan *Request error INTERNAL_ERROR* | MLflow 3 bloquea (403) los `POST` del navegador si su origen no está permitido | `--cors-allowed-origins=https://mlflow.bolsa-lab.site` |
| MLflow abre en una vista vacía | MLflow 3 arranca en la vista **GenAI** | Cambiar a **Model training**, arriba a la izquierda |
