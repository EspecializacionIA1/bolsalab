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
