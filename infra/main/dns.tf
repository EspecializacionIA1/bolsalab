# DNS del dominio en Route 53. El dominio sigue comprado en GoDaddy;
# allá solo se cambian los servidores DNS por los de esta zona.

resource "aws_route53_zone" "main" {
  name = var.domain
}

# Frontend y /api
resource "aws_route53_record" "root" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain
  type    = "A"
  ttl     = 300
  records = [aws_eip.server.public_ip]
}

resource "aws_route53_record" "mlflow" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "mlflow.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.server.public_ip]
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain}"
  type    = "CNAME"
  ttl     = 300
  records = [var.domain]
}

# Solo Let's Encrypt (el que usa Caddy) puede emitir certificados del dominio.
resource "aws_route53_record" "caa" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain
  type    = "CAA"
  ttl     = 3600
  records = ["0 issue \"letsencrypt.org\""]
}

# El dominio no envía correos: SPF y DMARC rechazan cualquiera que diga venir de él.
resource "aws_route53_record" "spf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain
  type    = "TXT"
  ttl     = 3600
  records = ["v=spf1 -all"]
}

resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${var.domain}"
  type    = "TXT"
  ttl     = 3600
  records = ["v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s"]
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# Con EKS la entrada ya no es la IP fija del servidor sino un ALB, que crea el
# controlador de balanceadores (eks_addons.tf) a partir de los Ingress.
# Cambian tres cosas:
#   1. Los registros "root" y "mlflow" de arriba apuntan al ALB con un alias
#      (se reemplazan por los de abajo).
#   2. HTTPS: el certificado lo da ACM, no Let's Encrypt (Caddy ya no está).
#      Por eso el registro CAA de arriba debe permitir también a Amazon:
#        records = ["0 issue \"letsencrypt.org\"", "0 issue \"amazon.com\""]
#   3. Los registros que no cambian: www, SPF y DMARC.

# resource "aws_acm_certificate" "main" {
#   domain_name               = var.domain
#   subject_alternative_names = ["www.${var.domain}", "mlflow.${var.domain}"]
#   validation_method         = "DNS"
#
#   lifecycle {
#     create_before_destroy = true
#   }
# }
#
# resource "aws_route53_record" "acm_validation" {
#   for_each = {
#     for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => dvo
#   }
#
#   zone_id         = aws_route53_zone.main.zone_id
#   name            = each.value.resource_record_name
#   type            = each.value.resource_record_type
#   ttl             = 300
#   records         = [each.value.resource_record_value]
#   allow_overwrite = true
# }
#
# resource "aws_acm_certificate_validation" "main" {
#   certificate_arn         = aws_acm_certificate.main.arn
#   validation_record_fqdns = [for r in aws_route53_record.acm_validation : r.fqdn]
# }
#
# # El ALB lo crea Kubernetes, no Terraform: se busca por las etiquetas que le
# # pone el controlador. Existe solo después de desplegar el primer Ingress del
# # grupo "bolsalab". (Alternativa: external-dns, que crea los registros solo.)
# data "aws_lb" "ingress" {
#   tags = {
#     "elbv2.k8s.aws/cluster" = var.project
#     "ingress.k8s.aws/stack" = "bolsalab"
#   }
# }
#
# # Reemplazan a aws_route53_record.root y aws_route53_record.mlflow de arriba.
# resource "aws_route53_record" "root_alb" {
#   zone_id = aws_route53_zone.main.zone_id
#   name    = var.domain
#   type    = "A"
#
#   alias {
#     name                   = data.aws_lb.ingress.dns_name
#     zone_id                = data.aws_lb.ingress.zone_id
#     evaluate_target_health = true
#   }
# }
#
# resource "aws_route53_record" "mlflow_alb" {
#   zone_id = aws_route53_zone.main.zone_id
#   name    = "mlflow.${var.domain}"
#   type    = "A"
#
#   alias {
#     name                   = data.aws_lb.ingress.dns_name
#     zone_id                = data.aws_lb.ingress.zone_id
#     evaluate_target_health = true
#   }
# }
