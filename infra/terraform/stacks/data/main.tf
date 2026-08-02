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
  description = "Private database subnets for the Happy Post sandbox Aurora cluster."
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

resource "aws_rds_cluster" "this" {
  cluster_identifier = "${local.name_prefix}-aurora-postgres"

  engine         = "aurora-postgresql"
  engine_version = "16.14"

  database_name   = var.db_name
  master_username = var.master_username
  master_password = random_password.database.result
  port            = 5432

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [data.terraform_remote_state.network.outputs.security_group_ids.database]
  storage_encrypted      = true

  backup_retention_period      = 1
  preferred_backup_window      = "15:30-16:00"
  preferred_maintenance_window = "sun:16:30-sun:17:00"
  apply_immediately            = false
  deletion_protection          = false
  skip_final_snapshot          = false
  final_snapshot_identifier    = "${local.name_prefix}-aurora-postgres-final-${random_id.final_snapshot.hex}"
  copy_tags_to_snapshot        = true

  lifecycle {
    precondition {
      condition     = var.aurora_serverless_min_capacity <= var.aurora_serverless_max_capacity
      error_message = "aurora_serverless_min_capacity must not exceed aurora_serverless_max_capacity."
    }
  }

  serverlessv2_scaling_configuration {
    min_capacity = var.aurora_serverless_min_capacity
    max_capacity = var.aurora_serverless_max_capacity
  }
}

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "${local.name_prefix}-aurora-postgres-writer-1"
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.this.engine
  engine_version     = aws_rds_cluster.this.engine_version

  publicly_accessible        = false
  auto_minor_version_upgrade = true
  apply_immediately          = false
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    dbname   = var.db_name
    host     = aws_rds_cluster.this.endpoint
    password = random_password.database.result
    port     = aws_rds_cluster.this.port
    username = var.master_username
  })
}
