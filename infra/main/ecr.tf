# ============================================================================
# ECR (PROPUESTA PARA EKS, TODO COMENTADO)
# ============================================================================
# Hoy las imágenes se construyen dentro del servidor (docker compose up --build).
# En EKS los nodos no construyen: descargan imágenes ya hechas. El CD las
# construye en GitHub Actions y las sube aquí.
#
#   api       backend/Dockerfile (FastAPI)
#   pipeline  imagen de las etapas de Airflow: bolsalab/ + uv.lock (a crear)
#   mlflow    deploy/mlflow/Dockerfile
#
# Etiquetas inmutables: cada imagen se etiqueta con el commit, y una etiqueta no
# se puede sobrescribir. Así se sabe exactamente qué código corre en el clúster.

# resource "aws_ecr_repository" "this" {
#   for_each = toset(["api", "pipeline", "mlflow"])
#
#   name                 = "${var.project}/${each.value}"
#   image_tag_mutability = "IMMUTABLE"
#   # Las imágenes se reconstruyen desde el repo, igual que los artefactos de MLflow.
#   force_delete = true
#
#   image_scanning_configuration {
#     scan_on_push = true
#   }
#
#   encryption_configuration {
#     encryption_type = "AES256"
#   }
# }
#
# # Solo las 10 imágenes más recientes de cada repositorio, para no acumular costo.
# resource "aws_ecr_lifecycle_policy" "this" {
#   for_each = aws_ecr_repository.this
#
#   repository = each.value.name
#
#   policy = jsonencode({
#     rules = [{
#       rulePriority = 1
#       description  = "Conserva las 10 imagenes mas recientes"
#       selection = {
#         tagStatus   = "any"
#         countType   = "imageCountMoreThan"
#         countNumber = 10
#       }
#       action = {
#         type = "expire"
#       }
#     }]
#   })
# }
