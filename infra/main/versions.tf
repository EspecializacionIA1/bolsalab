# El estado vive en el bucket que crea infra/bootstrap.

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "bolsa-lab-site-tfstate"
    key          = "main/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.project
      ManagedBy = "terraform"
    }
  }
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks_addons.tf
# ============================================================================
# Para instalar charts de Helm desde Terraform se suman dos proveedores dentro de
# required_providers (arriba), y después `terraform init -upgrade` para que
# .terraform.lock.hcl los registre:
#
#     helm = {
#       source  = "hashicorp/helm"
#       version = "~> 3.0"
#     }
#     kubernetes = {
#       source  = "hashicorp/kubernetes"
#       version = "~> 2.38"
#     }
