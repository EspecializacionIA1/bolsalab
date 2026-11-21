output "server_id" {
  description = "Id del servidor, para entrar con SSM"
  value       = aws_instance.server.id
}

output "server_ip" {
  description = "IP fija del servidor"
  value       = aws_eip.server.public_ip
}

output "artifacts_bucket" {
  description = "Bucket de artefactos de MLflow"
  value       = aws_s3_bucket.artifacts.id
}

output "connect_command" {
  description = "Comando para abrir una terminal en el servidor"
  value       = "aws ssm start-session --target ${aws_instance.server.id}"
}
