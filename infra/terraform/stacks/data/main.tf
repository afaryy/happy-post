locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Stack       = "stack-data"
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/foundations/network/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}

resource "aws_db_subnet_group" "this" {
  name        = "${local.name_prefix}-database"
  description = "Private database subnets for the Happy Post sandbox RDS instance."
  subnet_ids  = values(data.terraform_remote_state.network.outputs.database_subnet_ids)
}

resource "random_password" "database" {
  length           = 32
  special          = true
  override_special = "!#$%&*+-_"
}

resource "random_id" "final_snapshot" {
  byte_length = 4
}

resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "${local.name_prefix}-database-credentials"
  description             = "Credentials for the Happy Post sandbox PostgreSQL database."
  recovery_window_in_days = 7
}

resource "aws_db_instance" "this" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = "16.14"
  instance_class = "db.t4g.micro"

  db_name  = var.db_name
  username = var.master_username
  password = random_password.database.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [data.terraform_remote_state.network.outputs.security_group_ids.database]
  publicly_accessible    = false
  multi_az               = false

  storage_type          = "gp3"
  allocated_storage     = 20
  max_allocated_storage = 40
  storage_encrypted     = true

  backup_retention_period    = 1
  backup_window              = "15:30-16:00"
  maintenance_window         = "sun:16:30-sun:17:00"
  auto_minor_version_upgrade = true
  apply_immediately          = false
  deletion_protection        = false
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${local.name_prefix}-postgres-final-${random_id.final_snapshot.hex}"
  delete_automated_backups   = true
  copy_tags_to_snapshot      = true

  performance_insights_enabled = false
  monitoring_interval          = 0
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    dbname   = var.db_name
    host     = aws_db_instance.this.address
    password = random_password.database.result
    port     = aws_db_instance.this.port
    username = var.master_username
  })
}
