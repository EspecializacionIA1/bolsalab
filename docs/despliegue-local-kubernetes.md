# Despliegue local en Kubernetes (kind)

Cómo levantar en un computador el stack de MLOps de BolsaLAB sobre Kubernetes: MLflow, la API, Airflow con el flujo de entrenamiento y el monitoreo con Prometheus y Grafana. Es el ensayo local de la propuesta de EKS (`infra/main/eks*.tf`, todo comentado); lo que funciona aquí es lo que después se despliega en AWS.

Solo para pruebas: las contraseñas de los archivos son de juguete y nada queda expuesto fuera del computador.

## Qué queda corriendo

```
                         ┌───────────────────── clúster kind "dslab" (3 nodos) ─────────────────────┐
                         │                                                                          │
 navegador ─port-forward─┼─▶ bolsalab   api (FastAPI + modelo de la imagen)                         │
                         │                                                                          │
                         │   mlops      mlflow ──┬─ corridas y registro: postgres (base "mlflow")   │
                         │                       └─ artefactos: volumen mlflow-artifacts            │
                         │              postgres (bases "mlflow" y "airflow")                       │
                         │                                                                          │
                         │   airflow    scheduler, dag-processor, api-server, triggerer             │
                         │              cada etapa del flujo ─▶ un pod bolsalab/pipeline            │
                         │                 └─ volumen bolsalab-trabajo: data/ reports/ models/      │
                         │                                                                          │
                         │   monitoring Prometheus, Grafana, Alertmanager (kube-prometheus-stack)   │
                         └──────────────────────────────────────────────────────────────────────────┘
```

| Namespace | Qué corre | Cómo se instala | Archivo |
|---|---|---|---|
| `mlops` | Postgres 17 y el servidor de MLflow | `kubectl apply` | `deploy/k8s/local/stack-base.yaml` |
| `bolsalab` | La API | `kubectl apply` | `deploy/k8s/local/stack-base.yaml` |
| `monitoring` | Prometheus, Grafana, Alertmanager, kube-state-metrics, node-exporter | Helm, chart `kube-prometheus-stack` 93.9.0 | valores por defecto |
| `airflow` | Airflow 3.2.2 con KubernetesExecutor y el flujo `bolsalab_entrenamiento_k8s` | Helm, chart `airflow` 1.22.0 | `deploy/k8s/local/airflow-values.yaml` |
| `airflow` | Volumen de trabajo del flujo y pod `cargador` | `kubectl apply` | `deploy/k8s/local/pipeline-storage.yaml` |

Imágenes propias (se construyen en el computador y se cargan en kind; ninguna sale a un registro):

| Imagen | Dockerfile | Qué lleva |
|---|---|---|
| `bolsalab/api:dev` | `backend/Dockerfile` | La API y el modelo de `models/` |
| `bolsalab/mlflow:dev-pg3` | `deploy/mlflow/Dockerfile` + el driver de Postgres | Servidor de MLflow |
| `bolsalab/pipeline:dev` | `deploy/pipeline/Dockerfile` | `bolsalab/`, `tests/` y las dependencias de `uv.lock`. Sin datos |
| `bolsalab/airflow:dev` | `deploy/airflow/Dockerfile` | Airflow 3.2.2 con `deploy/airflow/dags/` adentro |

## 0. Requisitos

| Herramienta | Versión probada | Instalación |
|---|---|---|
| Docker Desktop | con **12 GB de memoria o más** (Settings → Resources) | docker.com |
| kind | 0.33 | `brew install kind` |
| kubectl | 1.34 (el clúster es 1.37) | `brew install kubectl` |
| Helm | 4.3 | `brew install helm` |

Opcional: `brew install k9s` para ver el clúster en la terminal.

Archivos que no están en git y hay que tener en el computador (licencias y Ley 1581):

- `data/external/crash/japan_panic_selling_2020/` con la encuesta (`pone.0315622.s001.xlsx`). Ver `docs/datos.md`.
- `reports/tuning.csv`, el resultado del ajuste por familias que eligió `xgboost|poda`. Lo produce el Ciclo 3B (`bolsalab.modeling.tuning`).

Todos los comandos se corren desde la raíz del repositorio.

## 1. Crear el clúster

```bash
kind create cluster --name dslab --config deploy/k8s/local/kind-config.yaml
kubectl config use-context kind-dslab
kubectl get nodes          # dslab-control-plane, dslab-worker, dslab-worker2 en Ready
```

kind trae la clase de almacenamiento `standard` (local-path): cada volumen vive en el disco de **un** nodo, y los pods que lo usan van siempre a ese nodo.

## 2. Construir y cargar las imágenes

```bash
# API (lleva el modelo de models/)
docker build -f backend/Dockerfile -t bolsalab/api:dev .

# MLflow con el driver de Postgres. SQLAlchemy usa psycopg (v3) para las
# direcciones postgresql://; con psycopg2-binary MLflow no arranca.
docker build -t bolsalab/mlflow:dev deploy/mlflow
docker build -t bolsalab/mlflow:dev-pg3 - <<'EOF'
FROM bolsalab/mlflow:dev
RUN uv pip install --system "psycopg[binary]"
EOF

# Etapas del flujo y Airflow con el flujo adentro
docker build -f deploy/pipeline/Dockerfile -t bolsalab/pipeline:dev .
docker build -t bolsalab/airflow:dev deploy/airflow

# kind no ve las imágenes de Docker: hay que cargarlas en sus nodos
for img in api:dev mlflow:dev-pg3 pipeline:dev airflow:dev; do
  kind load docker-image bolsalab/$img --name dslab
done
```

Para ver qué imágenes tiene un nodo: `docker exec dslab-worker crictl images | grep bolsalab`.

La imagen `pipeline` tarda unos 10 minutos la primera vez (xgboost, lightgbm, catboost, shap, mlflow).

## 3. Postgres, MLflow y la API

```bash
kubectl apply -f deploy/k8s/local/stack-base.yaml
kubectl -n mlops rollout status deploy/postgres
kubectl -n mlops rollout status deploy/mlflow
kubectl -n bolsalab rollout status deploy/api

# Base de datos de Airflow, en el mismo Postgres
kubectl -n mlops exec deploy/postgres -- \
  psql -U bolsalab -d mlflow -c "CREATE DATABASE airflow;"
```

Un `Readiness probe failed` de Postgres en el primer minuto es normal: la base todavía está arrancando.

Comprobar:

```bash
kubectl -n bolsalab port-forward svc/api 8000:8000 &
curl http://localhost:8000/api/health

kubectl -n mlops port-forward svc/mlflow 5000:5000 &
open http://localhost:5000
```

Para subir a MLflow el modelo que ya está en `models/`:

```bash
MLFLOW_TRACKING_URI=http://localhost:5000 uv run python -m bolsalab.modeling.mlflow_tracking
```

## 4. Monitoreo: Prometheus y Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kps prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace --version 93.9.0
kubectl -n monitoring get pods     # todos en Running después de 2-3 minutos
```

Sin configurar nada, Prometheus ya mide CPU, memoria, reinicios y pods caídos (`OOMKilled`, `CrashLoopBackOff`) de todo el clúster.

Entrar a Grafana:

```bash
# Contraseña del usuario admin
kubectl -n monitoring get secret -l app.kubernetes.io/name=grafana \
  -o jsonpath='{.items[0].data.admin-password}' | base64 -d; echo

kubectl -n monitoring port-forward svc/kps-grafana 3000:80
```

http://localhost:3000, usuario `admin`. Tableros útiles en **Dashboards**:

- **Kubernetes / Compute Resources / Namespace (Pods)**, con `airflow` mientras corre el flujo: memoria de cada etapa.
- **Kubernetes / Compute Resources / Node (Pods)**: si el clúster se está quedando sin memoria.

Prometheus directo: `kubectl -n monitoring port-forward svc/kps-kube-prometheus-stack-prometheus 9090` → http://localhost:9090.

## 5. Airflow

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm upgrade --install airflow apache-airflow/airflow -n airflow --create-namespace \
  --version 1.22.0 -f deploy/k8s/local/airflow-values.yaml --timeout 10m
kubectl -n airflow get pods        # api-server, scheduler, dag-processor y triggerer en Running
```

`airflow-values.yaml` usa el Postgres de `mlops` (no el que trae el chart), apaga Redis y StatsD (no hacen falta con KubernetesExecutor) y apunta a la imagen `bolsalab/airflow:dev`.

Entrar:

```bash
kubectl -n airflow port-forward svc/airflow-api-server 8080:8080
```

http://localhost:8080, usuario `admin` y contraseña `admin` (los del chart).

## 6. El flujo de entrenamiento

### Volumen de trabajo y datos

Las etapas comparten el volumen `bolsalab-trabajo`, montado en `data/`, `reports/` y `models/` de cada pod: lo que escribe una etapa lo lee la siguiente. La encuesta no va en la imagen; se sube al volumen con el pod `cargador`.

```bash
kubectl apply -f deploy/k8s/local/pipeline-storage.yaml
kubectl -n airflow wait --for=condition=Ready pod/cargador --timeout=120s

kubectl cp data/external/crash/japan_panic_selling_2020 \
  airflow/cargador:/trabajo/data/external/crash/japan_panic_selling_2020
kubectl cp reports/tuning.csv airflow/cargador:/trabajo/reports/tuning.csv

kubectl -n airflow exec cargador -- ls -R /trabajo | head -20
```

### Correrlo

En http://localhost:8080, **`bolsalab_entrenamiento_k8s`** → activar → **▶ Trigger**. En otra terminal:

```bash
kubectl -n airflow get pods -w
```

Cada etapa levanta dos pods: el trabajador de Airflow y `bolsalab-<etapa>`, que hace el trabajo.

| # | Etapa | Qué hace | Deja en el volumen |
|---|---|---|---|
| 1 | `verificar_fuente` | Revisa que estén la encuesta y `tuning.csv` | — |
| 2 | `preparar_datos` | `bolsalab.dataset` | `data/interim/japan_investors.parquet` |
| 3 | `validar_datos` | `pytest tests/test_dataset.py` | — |
| 4 | `construir_variables` | `bolsalab.features` | `data/processed/japan_training.parquet` |
| 5 | `validar_variables` | `pytest tests/test_features.py` | — |
| 6 | `comparar_modelos` | 7 modelos, validación anidada 5 × 3, solo el 80 % | `reports/benchmark.csv` |
| 7 | `compuerta_calidad` | Detiene el flujo si AUROC < 0,60, si el ganador no supera a la logística o si la pendiente de calibración sale de [0,8; 1,25] | — |
| 8 | `exportar_prototipo` | Entrena `xgboost\|poda`, lo exporta y lo registra en MLflow. Se salta si `models/` ya tiene el modelo medido en la prueba | `models/crash_reaction_v1.joblib` y `.json` |
| 9 | `desempeno_grupos` | `bolsalab.modeling.groups` | `reports/groups.csv` |
| 10 | `explicacion_shap` | `bolsalab.explain` | `reports/shap_*.csv`, `reports/figures/shap_*.png` |

El flujo nunca toca el 20 % de prueba: `train --final` no está en Kubernetes.

### Resultados

- **MLflow** (http://localhost:5000): experimento `bolsalab-modelo-final`, corrida con etiqueta `tipo=prototipo`, con parámetros, métricas, el `.joblib` y el `.json`. Un prototipo nunca crea versión en el registro `bolsalab-reaccion-caidas`; solo `--final` lo hace.
- **Archivos**: `kubectl cp airflow/cargador:/trabajo/reports ./reports-k8s`.

Si MLflow no responde, la etapa 8 queda en verde igual (el modelo ya está en el volumen). Revisar en su log que diga `Registrado en MLflow: corrida ...`.

## 7. Direcciones

Todos los servicios son `ClusterIP`: solo se llega a ellos desde dentro del clúster. Desde el computador se entra con `port-forward` (con kind en macOS, ni siquiera un NodePort se ve sin configuración extra).

| Servicio | Comando | Dirección | Usuario |
|---|---|---|---|
| API | `kubectl -n bolsalab port-forward svc/api 8000:8000` | http://localhost:8000/api/docs | — |
| MLflow | `kubectl -n mlops port-forward svc/mlflow 5000:5000` | http://localhost:5000 | — |
| Airflow | `kubectl -n airflow port-forward svc/airflow-api-server 8080:8080` | http://localhost:8080 | admin / admin |
| Grafana | `kubectl -n monitoring port-forward svc/kps-grafana 3000:80` | http://localhost:3000 | admin / ver sección 4 |
| Prometheus | `kubectl -n monitoring port-forward svc/kps-kube-prometheus-stack-prometheus 9090` | http://localhost:9090 | — |

Entre pods se usan los nombres internos: `mlflow.mlops.svc.cluster.local:5000`, `postgres.mlops.svc.cluster.local:5432`.

## 8. Cuando algo falla

**Dónde mirar, en orden:**

1. Airflow → la caja roja → **Logs**: trae la salida del pod, con el error de Python.
2. Los pods que fallan no se borran (solo los exitosos):
   ```bash
   kubectl -n airflow get pods
   kubectl -n airflow logs bolsalab-<etapa>-<id>
   kubectl -n airflow describe pod bolsalab-<etapa>-<id>   # OOMKilled, imagen, Pending
   ```
3. El volumen: `kubectl -n airflow exec cargador -- ls -la /trabajo/reports /trabajo/models`.
4. Corregido el problema, en Airflow: la etapa → **Clear** con **Downstream**. Repite desde ahí, sin volver a comparar modelos.

**Problemas que ya aparecieron:**

| Síntoma | Causa | Solución |
|---|---|---|
| MLflow en `CrashLoopBackOff`, `No module named 'psycopg'` | La imagen tenía `psycopg2-binary` y SQLAlchemy busca `psycopg` (v3) | Usar `bolsalab/mlflow:dev-pg3` (sección 2) |
| `exportar_prototipo` falla con `FileNotFoundError: /app/reports/tuning.csv` | El volumen no tenía `tuning.csv` y ninguna etapa lo produce | `kubectl cp reports/tuning.csv ...` (sección 6). Ahora `verificar_fuente` lo revisa al empezar |
| `ErrImageNeverPull` o `ImagePullBackOff` | La imagen no se cargó en kind | `kind load docker-image bolsalab/<imagen> --name dslab` |
| `OOMKilled` en una etapa | Se pasó del límite de memoria | Subir `memoria=` de esa etapa en el flujo y reconstruir `bolsalab/airflow:dev` |
| Pods en `Pending` con `Insufficient memory` | Docker Desktop con poca memoria | Subirla a 12 GB o más |
| `helm install` falla con `open airflow-values.yaml` | Ruta del archivo | Correr desde la raíz con `-f deploy/k8s/local/airflow-values.yaml` |
| Un port-forward deja de responder | Se reinició el pod | Volver a correr el `port-forward` |

## 9. Actualizar después de un cambio

| Cambió | Qué hacer |
|---|---|
| El flujo (`deploy/airflow/dags/`) | `docker build -t bolsalab/airflow:dev deploy/airflow`, `kind load ...` y `kubectl -n airflow rollout restart deploy` |
| El código de `bolsalab/` o `uv.lock` | Reconstruir y cargar `bolsalab/pipeline:dev`. La próxima corrida ya la usa |
| La API o el modelo de `models/` | Reconstruir y cargar `bolsalab/api:dev`, y `kubectl -n bolsalab rollout restart deploy/api` |
| `stack-base.yaml` | `kubectl apply -f deploy/k8s/local/stack-base.yaml` |
| `airflow-values.yaml` | El `helm upgrade --install` de la sección 5 |

Con la misma etiqueta (`:dev`), Kubernetes no se entera de que la imagen cambió: hace falta el `rollout restart`.

## 10. Apagar o borrar

```bash
# Detener sin perder nada: apagar Docker Desktop. Al volver, el clúster arranca solo.

# Borrar solo el flujo y sus datos
kubectl delete -f deploy/k8s/local/pipeline-storage.yaml

# Borrar todo el clúster (volúmenes, corridas de MLflow, bases de datos)
kind delete cluster --name dslab
```

## Diferencias con EKS

| Aquí (kind) | En EKS (propuesta de `infra/main/eks*.tf`) |
|---|---|
| Imágenes construidas en el computador y cargadas con `kind load` | Construidas por el CD en GitHub Actions y subidas a ECR, etiquetadas con el commit |
| Postgres en un pod | RDS (`storage.tf`) |
| Artefactos de MLflow en un volumen | El bucket S3 de hoy |
| Volumen de trabajo local-path (un nodo) | EFS, que varios nodos montan a la vez |
| Datos subidos con `kubectl cp` | Bucket privado de datos |
| Flujos copiados en la imagen de Airflow | git-sync desde el repositorio |
| `port-forward` | ALB con certificado de ACM (`bolsa-lab.site`); solo la API es pública |
| Contraseñas en los archivos | Secretos fuera del repositorio |

## Siguiente paso: logs centralizados

Hoy los logs de una etapa exitosa se pierden cuando se borra su pod. La propuesta es agregar **Loki** (guarda los logs) y **Grafana Alloy** (los recoge de cada pod) al namespace `monitoring`, y consultarlos en la misma Grafana, junto a las métricas de Prometheus. Todavía no está instalado.
