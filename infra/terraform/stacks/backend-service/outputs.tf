output "service_name" {
  description = "Backend ECS service name."
  value       = aws_ecs_service.backend.name
}

output "task_definition_arn" {
  description = "Initial backend task definition ARN. Later CI deployments register digest-pinned revisions."
  value       = aws_ecs_task_definition.backend.arn
}
