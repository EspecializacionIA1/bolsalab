output "state_bucket" {
  description = "Bucket que usa el backend de infra/main"
  value       = aws_s3_bucket.state.id
}
