# Aviso por correo al 80 % del gasto real y si el pronóstico del mes pasa el límite.

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# Con EKS el límite de USD 25 no alcanza. Costo aproximado al mes en us-east-1
# (revisar precios al activarlo):
#   Plano de control de EKS                        ~ USD 73  (USD 0,10 la hora, fijo)
#   2 nodos t3.large SPOT (ON_DEMAND ~ USD 120)    ~ USD 40 a 50
#   ALB                                            ~ USD 16 + tráfico
#   RDS db.t4g.micro con 20 GB                     ~ USD 14
#   EFS, ECR, S3, Route 53                         ~ USD 2 a 5
#   NAT Gateway, solo con subredes privadas        ~ USD 33 + tráfico
#   Total                                          ~ USD 150 a 190 (sin NAT)
#
# Opciones: subir budget_limit_usd (por ejemplo a 200) o crear el clúster solo
# para las demostraciones y destruirlo después (el estado de RDS y S3 se
# conserva; el plano de control y los nodos no cobran mientras no existen).
