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

variable "github_repo_immutable" {
  description = "El mismo repo con los ids de GitHub (dueño@id/nombre@id), como viene en el token OIDC"
  type        = string
  default     = "EspecializacionIA1@258116174/bolsalab@1354180301"
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

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================

# variable "eks_version" {
#   description = "Versión de Kubernetes del clúster (revisar las que EKS soporta al activarlo)"
#   type        = string
#   default     = "1.34"
# }
#
# variable "eks_node_instance_types" {
#   description = "Tipos de servidor de los nodos; varios ayudan a conseguir capacidad SPOT"
#   type        = list(string)
#   default     = ["t3.large", "t3a.large"]
# }
#
# variable "eks_node_capacity_type" {
#   description = "ON_DEMAND o SPOT (más barato, AWS puede retirar el nodo con aviso)"
#   type        = string
#   default     = "SPOT"
# }
#
# variable "eks_node_desired_size" {
#   description = "Nodos al crear el grupo"
#   type        = number
#   default     = 2
# }
#
# variable "eks_public_access_cidrs" {
#   description = "Desde dónde se llega a la API de Kubernetes (además se exige IAM)"
#   type        = list(string)
#   default     = ["0.0.0.0/0"]
# }
#
# variable "eks_admin_principal_arns" {
#   description = "Roles de IAM del equipo (IAM Identity Center) con acceso de administrador al clúster"
#   type        = list(string)
#   default     = []
# }
#
# variable "data_bucket_name" {
#   description = "Bucket de los datos fuente del flujo; debe ser único en todo AWS"
#   type        = string
#   default     = "bolsa-lab-site-data"
# }
