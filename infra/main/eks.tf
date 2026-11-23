# ============================================================================
# EKS (PROPUESTA, TODO COMENTADO)
# ============================================================================
# Cómo se vería BolsaLAB en Kubernetes (Amazon EKS) en vez del servidor único de
# server.tf. Nada de este archivo se aplica: está comentado para que el equipo lo
# revise. Para activarlo hay que descomentar, en este orden:
#   1. Las variables de EKS en variables.tf.
#   2. La segunda subred (public_b) en network.tf, porque EKS pide dos zonas.
#   3. Este archivo, ecr.tf y lo de EKS en storage.tf, github.tf y outputs.tf.
#   4. Subir el presupuesto en budget.tf: EKS cuesta bastante más que USD 25.
#   5. eks_addons.tf y dns.tf, en un segundo `terraform apply`, cuando el clúster
#      ya exista (el proveedor de Helm necesita el clúster para conectarse).
#
# Qué corre en el clúster (espacios de nombres):
#   bolsalab    API FastAPI (imagen de backend/Dockerfile) y la página del sitio
#   mlops       MLflow (base en RDS, modelos en el bucket de storage.tf) y Airflow
#   monitoring  Prometheus, Grafana y Alertmanager (kube-prometheus-stack)
#   kube-system Controlador de balanceadores (ALB) y drivers de discos (EBS, EFS)
#
# Permisos de los pods: EKS Pod Identity. Cada cuenta de servicio de Kubernetes
# recibe un rol de IAM propio, sin claves guardadas, igual que hoy el servidor.
# Reemplaza al rol único del servidor de iam.tf.

# ----------------------------------------------------------------------------
# Plano de control
# ----------------------------------------------------------------------------

# resource "aws_iam_role" "eks_cluster" {
#   name = "${var.project}-eks-cluster"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect    = "Allow"
#       Principal = { Service = "eks.amazonaws.com" }
#       Action    = ["sts:AssumeRole", "sts:TagSession"]
#     }]
#   })
# }
#
# resource "aws_iam_role_policy_attachment" "eks_cluster" {
#   role       = aws_iam_role.eks_cluster.name
#   policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
# }
#
# resource "aws_eks_cluster" "main" {
#   name     = var.project
#   version  = var.eks_version
#   role_arn = aws_iam_role.eks_cluster.arn
#
#   # Acceso con "access entries" de IAM (abajo), sin el ConfigMap aws-auth.
#   access_config {
#     authentication_mode                         = "API"
#     bootstrap_cluster_creator_admin_permissions = true
#   }
#
#   vpc_config {
#     subnet_ids              = [aws_subnet.public.id, aws_subnet.public_b.id]
#     endpoint_private_access = true
#     # Público para que lleguen el equipo y GitHub Actions; igual exige IAM.
#     endpoint_public_access = true
#     public_access_cidrs    = var.eks_public_access_cidrs
#   }
#
#   # Solo auditoría: cada tipo de log extra cuesta en CloudWatch.
#   enabled_cluster_log_types = ["audit"]
#
#   depends_on = [aws_iam_role_policy_attachment.eks_cluster]
# }

# ----------------------------------------------------------------------------
# Nodos
# ----------------------------------------------------------------------------
# Un solo grupo de nodos para todo. El entrenamiento tarda minutos en CPU, así
# que no hace falta un grupo aparte con GPU.
# Los nodos van en las subredes públicas para no pagar un NAT Gateway (unos
# USD 33 al mes). Con presupuesto, lo recomendable es la opción de subredes
# privadas con NAT que está comentada en network.tf.

# resource "aws_iam_role" "eks_nodes" {
#   name = "${var.project}-eks-nodes"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect    = "Allow"
#       Principal = { Service = "ec2.amazonaws.com" }
#       Action    = "sts:AssumeRole"
#     }]
#   })
# }
#
# resource "aws_iam_role_policy_attachment" "eks_nodes" {
#   for_each = toset([
#     "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
#     "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
#     "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
#     # Igual que el servidor de hoy: se entra a los nodos con SSM, sin SSH.
#     "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
#   ])
#
#   role       = aws_iam_role.eks_nodes.name
#   policy_arn = each.value
# }
#
# resource "aws_eks_node_group" "general" {
#   cluster_name    = aws_eks_cluster.main.name
#   node_group_name = "${var.project}-general"
#   node_role_arn   = aws_iam_role.eks_nodes.arn
#   subnet_ids      = [aws_subnet.public.id, aws_subnet.public_b.id]
#
#   # Airflow, MLflow y Prometheus juntos piden unos 6 a 8 GB de memoria.
#   instance_types = var.eks_node_instance_types
#   # SPOT cuesta cerca de un tercio; AWS puede quitar un nodo con 2 minutos de aviso.
#   capacity_type = var.eks_node_capacity_type
#   disk_size     = 30
#
#   scaling_config {
#     desired_size = var.eks_node_desired_size
#     min_size     = 1
#     max_size     = 3
#   }
#
#   update_config {
#     max_unavailable = 1
#   }
#
#   labels = {
#     workload = "general"
#   }
#
#   depends_on = [aws_iam_role_policy_attachment.eks_nodes]
#
#   # El autoescalado cambia desired_size; Terraform no debe devolverlo.
#   lifecycle {
#     ignore_changes = [scaling_config[0].desired_size]
#   }
# }

# ----------------------------------------------------------------------------
# Complementos de EKS
# ----------------------------------------------------------------------------

# resource "aws_eks_addon" "core" {
#   for_each = toset(["vpc-cni", "kube-proxy", "coredns", "eks-pod-identity-agent"])
#
#   cluster_name = aws_eks_cluster.main.name
#   addon_name   = each.value
#
#   # coredns necesita nodos donde correr.
#   depends_on = [aws_eks_node_group.general]
# }
#
# # Discos EBS (ReadWriteOnce): base de Airflow si va dentro del clúster y Prometheus.
# resource "aws_eks_addon" "ebs_csi" {
#   cluster_name = aws_eks_cluster.main.name
#   addon_name   = "aws-ebs-csi-driver"
#
#   pod_identity_association {
#     role_arn        = aws_iam_role.pod["ebs_csi"].arn
#     service_account = "ebs-csi-controller-sa"
#   }
#
#   depends_on = [aws_eks_addon.core]
# }
#
# # EFS (ReadWriteMany): la carpeta compartida entre las etapas del flujo de Airflow.
# # Hoy cada etapa le deja archivos a la siguiente en el disco local
# # (data/interim -> data/processed -> reports/ -> models/). En Kubernetes cada
# # etapa es un pod distinto, así que todas montan este mismo volumen.
# resource "aws_eks_addon" "efs_csi" {
#   cluster_name = aws_eks_cluster.main.name
#   addon_name   = "aws-efs-csi-driver"
#
#   pod_identity_association {
#     role_arn        = aws_iam_role.pod["efs_csi"].arn
#     service_account = "efs-csi-controller-sa"
#   }
#
#   depends_on = [aws_eks_addon.core]
# }

# ----------------------------------------------------------------------------
# Roles de los pods (EKS Pod Identity)
# ----------------------------------------------------------------------------
# Un rol por componente, con lo mínimo:
#   mlflow     lee y escribe los artefactos (el mismo bucket de storage.tf)
#   pipeline   pods de las etapas de Airflow: leen los datos fuente del bucket de
#              datos. Escriben en MLflow por HTTP, no directo en S3
#   lb         controlador de balanceadores (crea el ALB del Ingress)
#   ebs_csi    driver de discos EBS
#   efs_csi    driver de EFS
# La API no necesita rol: pide el modelo a MLflow por HTTP (--serve-artifacts).

# locals {
#   pod_identity_trust = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect    = "Allow"
#       Principal = { Service = "pods.eks.amazonaws.com" }
#       Action    = ["sts:AssumeRole", "sts:TagSession"]
#     }]
#   })
#
#   # componente => espacio de nombres y cuenta de servicio de Kubernetes
#   pod_identities = {
#     mlflow   = { namespace = "mlops", service_account = "mlflow" }
#     pipeline = { namespace = "mlops", service_account = "bolsalab-pipeline" }
#     lb       = { namespace = "kube-system", service_account = "aws-load-balancer-controller" }
#     ebs_csi  = { namespace = "kube-system", service_account = "ebs-csi-controller-sa" }
#     efs_csi  = { namespace = "kube-system", service_account = "efs-csi-controller-sa" }
#   }
# }
#
# resource "aws_iam_role" "pod" {
#   for_each = local.pod_identities
#
#   name               = "${var.project}-pod-${replace(each.key, "_", "-")}"
#   assume_role_policy = local.pod_identity_trust
# }
#
# resource "aws_iam_role_policy_attachment" "pod_managed" {
#   for_each = {
#     ebs_csi = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
#     efs_csi = "arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy"
#   }
#
#   role       = aws_iam_role.pod[each.key].name
#   policy_arn = each.value
# }
#
# # Lo mismo que hoy tiene el servidor en iam.tf para MLflow.
# resource "aws_iam_role_policy" "pod_mlflow" {
#   name = "${var.project}-pod-mlflow"
#   role = aws_iam_role.pod["mlflow"].id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid      = "MlflowArtifactsList"
#         Effect   = "Allow"
#         Action   = ["s3:ListBucket"]
#         Resource = aws_s3_bucket.artifacts.arn
#       },
#       {
#         Sid      = "MlflowArtifactsObjects"
#         Effect   = "Allow"
#         Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
#         Resource = "${aws_s3_bucket.artifacts.arn}/*"
#       }
#     ]
#   })
# }
#
# # Solo lectura de los datos fuente (bucket de datos en storage.tf).
# resource "aws_iam_role_policy" "pod_pipeline" {
#   name = "${var.project}-pod-pipeline"
#   role = aws_iam_role.pod["pipeline"].id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid      = "SourceDataList"
#         Effect   = "Allow"
#         Action   = ["s3:ListBucket"]
#         Resource = aws_s3_bucket.data.arn
#       },
#       {
#         Sid      = "SourceDataRead"
#         Effect   = "Allow"
#         Action   = ["s3:GetObject"]
#         Resource = "${aws_s3_bucket.data.arn}/*"
#       }
#     ]
#   })
# }
#
# # La política del controlador de balanceadores es larga y la publica AWS.
# # Se descarga una vez junto a este archivo:
# #   curl -o iam/aws-load-balancer-controller.json \
# #     https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/<versión>/docs/install/iam_policy.json
# resource "aws_iam_role_policy" "pod_lb" {
#   name   = "${var.project}-pod-lb"
#   role   = aws_iam_role.pod["lb"].id
#   policy = file("${path.module}/iam/aws-load-balancer-controller.json")
# }
#
# # ebs_csi y efs_csi se asocian dentro de su complemento (arriba).
# resource "aws_eks_pod_identity_association" "this" {
#   for_each = {
#     for name, id in local.pod_identities : name => id if !contains(["ebs_csi", "efs_csi"], name)
#   }
#
#   cluster_name    = aws_eks_cluster.main.name
#   namespace       = each.value.namespace
#   service_account = each.value.service_account
#   role_arn        = aws_iam_role.pod[each.key].arn
# }

# ----------------------------------------------------------------------------
# Quién entra al clúster
# ----------------------------------------------------------------------------

# # El equipo (roles de IAM Identity Center) como administradores.
# resource "aws_eks_access_entry" "admins" {
#   for_each = toset(var.eks_admin_principal_arns)
#
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = each.value
# }
#
# resource "aws_eks_access_policy_association" "admins" {
#   for_each = toset(var.eks_admin_principal_arns)
#
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = each.value
#   policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
#
#   access_scope {
#     type = "cluster"
#   }
#
#   depends_on = [aws_eks_access_entry.admins]
# }
#
# # El CD de GitHub (rol de github.tf): solo puede desplegar en "bolsalab" y "mlops".
# # Reemplaza al SSM de hoy: en vez de git pull en el servidor, hace helm upgrade.
# resource "aws_eks_access_entry" "github_deploy" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_iam_role.github_deploy.arn
# }
#
# resource "aws_eks_access_policy_association" "github_deploy" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_iam_role.github_deploy.arn
#   policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
#
#   access_scope {
#     type       = "namespace"
#     namespaces = ["bolsalab", "mlops"]
#   }
#
#   depends_on = [aws_eks_access_entry.github_deploy]
# }
