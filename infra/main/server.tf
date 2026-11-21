# Servidor único: Docker corre Caddy, FastAPI, MLflow y el frontend.

data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# Solo web. Sin puerto 22: se entra con SSM.
resource "aws_security_group" "server" {
  name        = "${var.project}-server"
  description = "HTTP y HTTPS publicos"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP (Caddy lo redirige a HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida libre (imagenes, certificados, S3)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "server" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.server.id]
  iam_instance_profile   = aws_iam_instance_profile.server.name
  user_data              = file("${path.module}/user_data.sh")

  # Arranca cuando ya hay salida a internet; si no, user_data no descarga Docker.
  depends_on = [aws_route_table_association.public]

  # Si usa mucha CPU se vuelve lento, pero no cobra de más.
  credit_specification {
    cpu_credits = "standard"
  }

  # Solo IMDSv2: los metadatos del servidor piden token.
  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_size = var.disk_size_gb
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.project}-server"
  }

  # Una AMI nueva de Amazon no debe reemplazar el servidor.
  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_eip" "server" {
  instance = aws_instance.server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project}-server"
  }
}
