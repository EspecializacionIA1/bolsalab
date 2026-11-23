# Red mínima: una VPC con una subred pública y salida a internet.

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = var.project
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = var.project
  }
}

# Zona "a": en us-east-1 no todas las zonas tienen t3.
# IP pública desde el arranque para que user_data pueda descargar Docker antes de recibir la IP fija.
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project}-public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project}-public"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ============================================================================
# EKS (PROPUESTA, COMENTADO): ver eks.tf
# ============================================================================
# EKS exige subredes en al menos dos zonas, y el controlador de balanceadores
# busca las subredes por etiquetas. Para activarlo:
#   1. Agregar a aws_subnet.public (arriba) estas dos etiquetas:
#        "kubernetes.io/role/elb"               = "1"
#        "kubernetes.io/cluster/${var.project}" = "shared"
#   2. Descomentar la segunda subred pública, en la zona "b".

# resource "aws_subnet" "public_b" {
#   vpc_id                  = aws_vpc.main.id
#   cidr_block              = "10.20.2.0/24"
#   availability_zone       = "${var.region}b"
#   map_public_ip_on_launch = true
#
#   tags = {
#     Name                                   = "${var.project}-public-b"
#     "kubernetes.io/role/elb"               = "1"
#     "kubernetes.io/cluster/${var.project}" = "shared"
#   }
# }
#
# resource "aws_route_table_association" "public_b" {
#   subnet_id      = aws_subnet.public_b.id
#   route_table_id = aws_route_table.public.id
# }

# Opción recomendada si hay presupuesto: nodos en subredes privadas, sin IP
# pública, que salen a internet por un NAT Gateway (unos USD 33 al mes más el
# tráfico). Con esto, eks.tf usaría las subredes privadas para los nodos y las
# públicas solo para el ALB.

# resource "aws_subnet" "private" {
#   for_each = { a = "10.20.11.0/24", b = "10.20.12.0/24" }
#
#   vpc_id            = aws_vpc.main.id
#   cidr_block        = each.value
#   availability_zone = "${var.region}${each.key}"
#
#   tags = {
#     Name                                   = "${var.project}-private-${each.key}"
#     "kubernetes.io/role/internal-elb"      = "1"
#     "kubernetes.io/cluster/${var.project}" = "shared"
#   }
# }
#
# resource "aws_eip" "nat" {
#   domain = "vpc"
#
#   tags = {
#     Name = "${var.project}-nat"
#   }
# }
#
# # Uno solo, en la zona "a", para ahorrar. Si esa zona cae, los nodos pierden salida.
# resource "aws_nat_gateway" "main" {
#   allocation_id = aws_eip.nat.id
#   subnet_id     = aws_subnet.public.id
#
#   tags = {
#     Name = var.project
#   }
#
#   depends_on = [aws_internet_gateway.main]
# }
#
# resource "aws_route_table" "private" {
#   vpc_id = aws_vpc.main.id
#
#   route {
#     cidr_block     = "0.0.0.0/0"
#     nat_gateway_id = aws_nat_gateway.main.id
#   }
#
#   tags = {
#     Name = "${var.project}-private"
#   }
# }
#
# resource "aws_route_table_association" "private" {
#   for_each = aws_subnet.private
#
#   subnet_id      = each.value.id
#   route_table_id = aws_route_table.private.id
# }
