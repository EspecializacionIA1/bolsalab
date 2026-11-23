# Permiso para que GitHub Actions despliegue en el servidor, sin claves guardadas.
# GitHub pide credenciales temporales con OIDC cada vez que corre el CD.

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Solo este repo y solo desde la rama main pueden usar el rol: un fork o un PR no.
resource "aws_iam_role" "github_deploy" {
  name = "${var.project}-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          # GitHub usa el formato "inmutable" (nombre@id), que impide reusar el permiso si
          # alguien recrea un repo con el mismo nombre. Se acepta también el formato clásico.
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo_immutable}:ref:refs/heads/main",
            "repo:${var.github_repo}:ref:refs/heads/main",
          ]
        }
      }
    }]
  })
}

# Lo único que puede hacer: mandar comandos SSM a este servidor y leer su resultado.
resource "aws_iam_role_policy" "github_deploy" {
  name = "${var.project}-github-deploy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RunCommandOnServer"
        Effect = "Allow"
        Action = "ssm:SendCommand"
        Resource = [
          aws_instance.server.arn,
          "arn:aws:ssm:${var.region}::document/AWS-RunShellScript",
        ]
      },
      {
        # Esta acción de AWS no se puede limitar a un recurso.
        Sid      = "ReadCommandResult"
        Effect   = "Allow"
        Action   = "ssm:GetCommandInvocation"
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# Hoy el CD manda un comando SSM al servidor (git pull + deploy/start.sh). Con
# EKS el CD cambia a:
#   1. Construir las imágenes en GitHub Actions y subirlas a ECR (ecr.tf),
#      etiquetadas con el commit.
#   2. `aws eks update-kubeconfig` y `helm upgrade` en los espacios "bolsalab" y
#      "mlops". El permiso dentro del clúster lo da la access entry de eks.tf.
# El rol y su condición de OIDC (solo main de este repo) no cambian; se le suma
# esta política, y la de SSM de arriba se borra cuando el servidor desaparezca.

# resource "aws_iam_role_policy" "github_deploy_eks" {
#   name = "${var.project}-github-deploy-eks"
#   role = aws_iam_role.github_deploy.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         # Esta acción de AWS no se puede limitar a un recurso.
#         Sid      = "EcrLogin"
#         Effect   = "Allow"
#         Action   = "ecr:GetAuthorizationToken"
#         Resource = "*"
#       },
#       {
#         Sid    = "PushImages"
#         Effect = "Allow"
#         Action = [
#           "ecr:BatchCheckLayerAvailability",
#           "ecr:BatchGetImage",
#           "ecr:CompleteLayerUpload",
#           "ecr:InitiateLayerUpload",
#           "ecr:PutImage",
#           "ecr:UploadLayerPart",
#         ]
#         Resource = [for repo in aws_ecr_repository.this : repo.arn]
#       },
#       {
#         # Lo único que pide `aws eks update-kubeconfig`.
#         Sid      = "DescribeCluster"
#         Effect   = "Allow"
#         Action   = "eks:DescribeCluster"
#         Resource = aws_eks_cluster.main.arn
#       }
#     ]
#   })
# }
