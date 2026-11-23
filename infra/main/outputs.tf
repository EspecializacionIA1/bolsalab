output "server_id" {
  description = "Id del servidor, para entrar con SSM"
  value       = aws_instance.server.id
}

output "deploy_role_arn" {
  description = "Rol que usa el CD de GitHub Actions (variable AWS_DEPLOY_ROLE_ARN del repo)"
  value       = aws_iam_role.github_deploy.arn
}

output "server_ip" {
  description = "IP fija del servidor"
  value       = aws_eip.server.public_ip
}

output "artifacts_bucket" {
  description = "Bucket de artefactos de MLflow"
  value       = aws_s3_bucket.artifacts.id
}

output "name_servers" {
  description = "Los 4 servidores DNS que van en GoDaddy"
  value       = aws_route53_zone.main.name_servers
}

output "connect_command" {
  description = "Comando para abrir una terminal en el servidor"
  value       = "aws ssm start-session --target ${aws_instance.server.id}"
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# server_id, server_ip y connect_command se borran cuando el servidor desaparezca.

# output "eks_cluster_name" {
#   description = "Nombre del clúster"
#   value       = aws_eks_cluster.main.name
# }
#
# output "kubeconfig_command" {
#   description = "Comando para que kubectl y helm se conecten al clúster"
#   value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.main.name}"
# }
#
# output "ecr_repositories" {
#   description = "Dirección de cada repositorio de imágenes (para el CD)"
#   value       = { for name, repo in aws_ecr_repository.this : name => repo.repository_url }
# }
#
# output "mlops_db_endpoint" {
#   description = "Postgres de MLflow y Airflow (la contraseña está en Secrets Manager)"
#   value       = aws_db_instance.mlops.endpoint
# }
#
# output "mlops_db_secret_arn" {
#   description = "Secreto con la contraseña de Postgres"
#   value       = aws_db_instance.mlops.master_user_secret[0].secret_arn
# }
#
# output "pipeline_efs_id" {
#   description = "Volumen compartido de las etapas de Airflow (para su StorageClass)"
#   value       = aws_efs_file_system.pipeline.id
# }
