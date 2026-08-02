output "db_cluster_identifier" {
  description = "Aurora PostgreSQL cluster identifier."
  value       = aws_rds_cluster.this.cluster_identifier
}

output "db_cluster_endpoint" {
  description = "Private Aurora PostgreSQL writer endpoint and port."
  value       = aws_rds_cluster.this.endpoint
}

output "db_subnet_group_name" {
  description = "Private database subnet-group name."
  value       = aws_db_subnet_group.this.name
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret; the secret value is never output."
  value       = aws_secretsmanager_secret.database_credentials.arn
}
