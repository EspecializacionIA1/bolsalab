variable "region" {
  description = "Región de AWS del proyecto"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Prefijo de nombres y etiqueta de todos los recursos"
  type        = string
  default     = "bolsalab"
}

variable "domain" {
  description = "Dominio de la app"
  type        = string
  default     = "bolsa-lab.site"
}

variable "github_repo" {
  description = "Repo de GitHub que puede desplegar (dueño/nombre)"
  type        = string
  default     = "EspecializacionIA1/bolsalab"
}

variable "instance_type" {
  description = "Tamaño del servidor"
  type        = string
  default     = "t3.small"
}

variable "disk_size_gb" {
  description = "Tamaño del disco del servidor"
  type        = number
  default     = 20
}

variable "artifacts_bucket_name" {
  description = "Bucket de artefactos de MLflow; debe ser único en todo AWS"
  type        = string
  default     = "bolsa-lab-site-mlflow-artifacts"
}

variable "budget_limit_usd" {
  description = "Límite mensual de gasto antes de avisar"
  type        = number
  default     = 25
}

variable "budget_email" {
  description = "Correo que recibe los avisos del presupuesto (va en terraform.tfvars, que no se versiona)"
  type        = string
}
