output "service_name" {
  description = "Frontend ECS service name."
  value       = aws_ecs_service.frontend.name
}

output "task_definition_arn" {
  description = "Initial frontend task definition ARN. Later CI deployments register digest-pinned revisions."
  value       = aws_ecs_task_definition.frontend.arn
}
