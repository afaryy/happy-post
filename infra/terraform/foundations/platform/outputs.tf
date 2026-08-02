output "ecs_cluster_arn" {
  description = "ARN of the shared Happy Post ECS cluster."
  value       = aws_ecs_cluster.this.arn
}

output "ecs_cluster_name" {
  description = "Name of the shared Happy Post ECS cluster."
  value       = aws_ecs_cluster.this.name
}

output "frontend_repository" {
  description = "Private frontend ECR repository details."
  value = {
    arn            = aws_ecr_repository.frontend.arn
    name           = aws_ecr_repository.frontend.name
    repository_url = aws_ecr_repository.frontend.repository_url
  }
}

output "backend_repository" {
  description = "Private backend ECR repository details."
  value = {
    arn            = aws_ecr_repository.backend.arn
    name           = aws_ecr_repository.backend.name
    repository_url = aws_ecr_repository.backend.repository_url
  }
}

output "frontend_log_group_name" {
  description = "CloudWatch Logs group for the frontend ECS service."
  value       = aws_cloudwatch_log_group.frontend.name
}

output "backend_log_group_name" {
  description = "CloudWatch Logs group for the backend ECS service."
  value       = aws_cloudwatch_log_group.backend.name
}

output "frontend_task_role_arn" {
  description = "Task role with no application AWS API permissions."
  value       = aws_iam_role.frontend_task.arn
}

output "backend_task_role_arn" {
  description = "Task role with no application AWS API permissions."
  value       = aws_iam_role.backend_task.arn
}

output "frontend_execution_role_arn" {
  description = "Execution role scoped to frontend image pulls and log publishing."
  value       = aws_iam_role.frontend_execution.arn
}

output "backend_execution_role_arn" {
  description = "Execution role scoped to backend image pulls and log publishing; service stack adds named-secret access."
  value       = aws_iam_role.backend_execution.arn
}
