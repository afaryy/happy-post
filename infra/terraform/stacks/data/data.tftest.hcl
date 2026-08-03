mock_provider "aws" {}

override_data {
  target = data.terraform_remote_state.network

  values = {
    outputs = {
      database_subnet_ids = {
        "0" = "subnet-0123456789abcdef0"
        "1" = "subnet-0123456789abcdef1"
      }
      security_group_ids = {
        database = "sg-0123456789abcdef0"
      }
    }
  }
}

run "data_stack_static_database_controls" {
  command = apply

  assert {
    condition     = aws_db_subnet_group.this.name == "happy-post-sandbox-database" && length(aws_db_subnet_group.this.subnet_ids) == 2
    error_message = "The data stack must create the approved private database subnet group across two database subnets."
  }

  assert {
    condition     = aws_db_instance.this.engine == "postgres" && aws_db_instance.this.engine_version == "16.14" && aws_db_instance.this.instance_class == "db.t4g.micro"
    error_message = "The sandbox database must stay on the approved PostgreSQL 16.14 db.t4g.micro configuration."
  }

  assert {
    condition     = aws_db_instance.this.publicly_accessible == false && aws_db_instance.this.multi_az == false
    error_message = "The sandbox database must remain private and Single-AZ."
  }

  assert {
    condition     = aws_db_instance.this.storage_type == "gp3" && aws_db_instance.this.allocated_storage == 20 && aws_db_instance.this.max_allocated_storage == 40 && aws_db_instance.this.storage_encrypted
    error_message = "The sandbox database must keep encrypted gp3 storage with the approved 20-40 GiB range."
  }

  assert {
    condition     = aws_db_instance.this.backup_retention_period == 1 && aws_db_instance.this.backup_window == "15:30-16:00" && aws_db_instance.this.maintenance_window == "sun:16:30-sun:17:00"
    error_message = "The sandbox database must keep the approved one-day retention and documented windows."
  }

  assert {
    condition     = aws_db_instance.this.skip_final_snapshot == false && aws_db_instance.this.deletion_protection == false && aws_db_instance.this.copy_tags_to_snapshot
    error_message = "Destroy safety must keep final snapshots and copied tags while retaining sandbox deletion protection off."
  }

  assert {
    condition     = aws_secretsmanager_secret.database_credentials.name == "happy-post-sandbox-database-credentials" && aws_secretsmanager_secret.database_credentials.recovery_window_in_days == 7
    error_message = "The database secret must keep the approved fixed name and seven-day recovery window."
  }
}

run "data_stack_rejects_non_sandbox_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}
