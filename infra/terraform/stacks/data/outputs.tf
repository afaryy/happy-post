output "db_instance_identifier" {
  description = "RDS PostgreSQL instance identifier."
  value       = aws_db_instance.this.identifier
}

output "db_instance_endpoint" {
  description = "Private RDS PostgreSQL endpoint and port."
  value       = aws_db_instance.this.endpoint
}

output "db_subnet_group_name" {
  description = "Private database subnet-group name."
  value       = aws_db_subnet_group.this.name
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret; the secret value is never output."
  value       = aws_secretsmanager_secret.database_credentials.arn
}
