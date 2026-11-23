# ============================================================================
# HELM SOBRE EKS (PROPUESTA, TODO COMENTADO)
# ============================================================================
# Lo que se instala dentro del clúster. Va en un segundo `terraform apply`,
# cuando el clúster de eks.tf ya existe: el proveedor de Helm necesita
# conectarse a él. (Alternativa más limpia: mover esto a su propia carpeta,
# infra/k8s, con su propio estado.)
#
# Reparto de responsabilidades recomendado:
#   Terraform (aquí)  lo que es del clúster y cambia poco: controlador de
#                     balanceadores y monitoreo.
#   CD de GitHub      lo que es de la app y cambia con cada merge: API, MLflow y
#                     Airflow, con `helm upgrade` y sus valores en deploy/k8s/
#                     (carpeta a crear). Así un cambio de la API no pasa por
#                     Terraform.
#
# Antes de activar: fijar la versión exacta de cada chart (campo version) y
# agregar los proveedores helm y kubernetes en versions.tf.

# provider "helm" {
#   kubernetes = {
#     host                   = aws_eks_cluster.main.endpoint
#     cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
#     exec = {
#       api_version = "client.authentication.k8s.io/v1beta1"
#       command     = "aws"
#       args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.main.name]
#     }
#   }
# }

# ----------------------------------------------------------------------------
# Controlador de balanceadores: crea el ALB a partir de los Ingress
# ----------------------------------------------------------------------------
# Reemplaza a Caddy en su papel de puerta de entrada: el ALB recibe el tráfico
# en 443 con el certificado de ACM (dns.tf) y lo reparte a la API, al sitio y a
# MLflow. Todos los Ingress usan el grupo "bolsalab" para compartir un solo ALB
# (cada ALB cuesta unos USD 16 al mes).

# resource "helm_release" "aws_load_balancer_controller" {
#   name       = "aws-load-balancer-controller"
#   namespace  = "kube-system"
#   repository = "https://aws.github.io/eks-charts"
#   chart      = "aws-load-balancer-controller"
#   # version  = "<fijar>"
#
#   set = [
#     { name = "clusterName", value = aws_eks_cluster.main.name },
#     { name = "region", value = var.region },
#     { name = "vpcId", value = aws_vpc.main.id },
#     { name = "serviceAccount.name", value = "aws-load-balancer-controller" },
#   ]
#
#   depends_on = [aws_eks_pod_identity_association.this, aws_eks_node_group.general]
# }

# ----------------------------------------------------------------------------
# Monitoreo: Prometheus, Grafana y Alertmanager
# ----------------------------------------------------------------------------
# Prometheus lee /metrics de la API (predicciones por tercio, avisos de fuera de
# rango, latencia y errores), las métricas de Airflow y el estado de los pods.
# Solo números agregados: ninguna respuesta del cuestionario ni datos de
# personas (Ley 1581 de 2012).

# resource "helm_release" "monitoring" {
#   name             = "kube-prometheus-stack"
#   namespace        = "monitoring"
#   create_namespace = true
#   repository       = "https://prometheus-community.github.io/helm-charts"
#   chart            = "kube-prometheus-stack"
#   # version        = "<fijar>"
#
#   # Retención corta y disco pequeño: es un prototipo.
#   values = [yamlencode({
#     prometheus = {
#       prometheusSpec = {
#         retention = "15d"
#         storageSpec = {
#           volumeClaimTemplate = {
#             spec = {
#               accessModes = ["ReadWriteOnce"]
#               resources   = { requests = { storage = "10Gi" } }
#             }
#           }
#         }
#       }
#     }
#   })]
#
#   depends_on = [aws_eks_addon.ebs_csi]
# }

# ----------------------------------------------------------------------------
# Lo que despliega el CD (referencia; no va en Terraform)
# ----------------------------------------------------------------------------
# MLflow    Imagen de ECR (deploy/mlflow). Base de datos: RDS de storage.tf en
#           vez del SQLite de hoy (varios pods no pueden compartir un archivo
#           SQLite). Artefactos: el mismo bucket. Contraseña: Caddy ya no está,
#           así que se usa la autenticación propia de MLflow
#           (`mlflow server --app-name basic-auth`) o un oauth2-proxy delante.
#
# Airflow   Chart oficial (https://airflow.apache.org, chart "airflow") con
#           KubernetesExecutor: cada tarea es un pod. Los flujos de
#           notebooks/4_mlops cambian BashOperator por KubernetesPodOperator con
#           la imagen "pipeline" de ECR, la cuenta de servicio bolsalab-pipeline
#           y el volumen EFS montado en data/, reports/ y models/. Su base de
#           datos: otra base ("airflow") en la misma instancia RDS.
#
# API       Deployment + Service + Ingress en "bolsalab". Carga el modelo desde
#           MLflow por alias (models:/bolsalab-reaccion-caidas@champion) en vez
#           de copiarlo dentro de la imagen. El límite por IP sigue funcionando:
#           el ALB también manda X-Forwarded-For.
