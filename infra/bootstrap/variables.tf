variable "region" {
  description = "Región de AWS del proyecto"
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Nombre del bucket del estado; debe ser único en todo AWS"
  type        = string
  default     = "bolsa-lab-site-tfstate"
}
