# Artefactos de MLflow (modelos y archivos de cada corrida).
# Se pueden volver a subir desde el repo, por eso se borra junto con la infraestructura.

resource "aws_s3_bucket" "artifacts" {
  bucket        = var.artifacts_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# El bucket de artefactos de arriba se queda igual: MLflow lo sigue usando desde
# el clúster con el rol "mlflow" de eks.tf. Se suman tres cosas.

# ----------------------------------------------------------------------------
# 1. Postgres (RDS) para MLflow y Airflow
# ----------------------------------------------------------------------------
# Hoy MLflow guarda las corridas en SQLite, en el disco del servidor. En el
# clúster un pod puede moverse de nodo y varios pods no pueden compartir un
# archivo SQLite. Una instancia pequeña sirve a los dos: base "mlflow" y base
# "airflow" (la segunda se crea al instalar Airflow).

# resource "aws_security_group" "mlops_db" {
#   name        = "${var.project}-mlops-db"
#   description = "Postgres solo desde los pods del cluster"
#   vpc_id      = aws_vpc.main.id
#
#   ingress {
#     description     = "Postgres desde el cluster"
#     from_port       = 5432
#     to_port         = 5432
#     protocol        = "tcp"
#     security_groups = [aws_eks_cluster.main.vpc_config[0].cluster_security_group_id]
#   }
# }
#
# resource "aws_db_subnet_group" "mlops" {
#   name       = "${var.project}-mlops"
#   subnet_ids = [aws_subnet.public.id, aws_subnet.public_b.id]
# }
#
# resource "aws_db_instance" "mlops" {
#   identifier        = "${var.project}-mlops"
#   engine            = "postgres"
#   engine_version    = "17"
#   instance_class    = "db.t4g.micro"
#   allocated_storage = 20
#   storage_type      = "gp3"
#   storage_encrypted = true
#
#   db_name  = "mlflow"
#   username = "bolsalab"
#   # AWS crea la contraseña y la guarda en Secrets Manager; nunca pasa por git.
#   manage_master_user_password = true
#
#   db_subnet_group_name   = aws_db_subnet_group.mlops.name
#   vpc_security_group_ids = [aws_security_group.mlops_db.id]
#   # Está en una subred pública, pero sin IP pública: solo llegan los pods.
#   publicly_accessible = false
#
#   backup_retention_period = 7
#   # Las corridas y el registro de modelos no se pueden recrear: se protegen.
#   deletion_protection       = true
#   skip_final_snapshot       = false
#   final_snapshot_identifier = "${var.project}-mlops-final"
# }

# ----------------------------------------------------------------------------
# 2. EFS: la carpeta compartida entre las etapas de Airflow
# ----------------------------------------------------------------------------
# Cada etapa (dataset, features, train, groups, explain) corre en su propio pod
# y le deja archivos a la siguiente. Todas montan este volumen en data/,
# reports/ y models/, como hoy en un solo disco.

# resource "aws_security_group" "efs" {
#   name        = "${var.project}-efs"
#   description = "NFS solo desde los pods del cluster"
#   vpc_id      = aws_vpc.main.id
#
#   ingress {
#     description     = "NFS desde el cluster"
#     from_port       = 2049
#     to_port         = 2049
#     protocol        = "tcp"
#     security_groups = [aws_eks_cluster.main.vpc_config[0].cluster_security_group_id]
#   }
# }
#
# resource "aws_efs_file_system" "pipeline" {
#   creation_token = "${var.project}-pipeline"
#   encrypted      = true
#
#   # Lo que no se usa en 30 días pasa a la clase más barata.
#   lifecycle_policy {
#     transition_to_ia = "AFTER_30_DAYS"
#   }
#
#   tags = {
#     Name = "${var.project}-pipeline"
#   }
# }
#
# resource "aws_efs_mount_target" "pipeline" {
#   for_each = { a = aws_subnet.public.id, b = aws_subnet.public_b.id }
#
#   file_system_id  = aws_efs_file_system.pipeline.id
#   subnet_id       = each.value
#   security_groups = [aws_security_group.efs.id]
# }

# ----------------------------------------------------------------------------
# 3. Bucket de datos fuente
# ----------------------------------------------------------------------------
# data/ no va en git por las licencias. El primer paso del flujo
# (verificar_fuente) copia de aquí al volumen EFS.
# OJO: solo datos cuya licencia permita guardarlos en la nube del proyecto. Los
# de la NFCS no van aquí: los términos de FINRA prohíben compartirlos.
# Sin force_destroy, a diferencia del bucket de artefactos: estos archivos no se
# pueden recrear desde el repo.

# resource "aws_s3_bucket" "data" {
#   bucket = var.data_bucket_name
# }
#
# resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
#   bucket = aws_s3_bucket.data.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }
#
# resource "aws_s3_bucket_public_access_block" "data" {
#   bucket = aws_s3_bucket.data.id
#
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }
