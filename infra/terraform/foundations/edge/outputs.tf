output "application_domain" {
  description = "Public Happy Post application domain."
  value       = var.application_domain
}

output "alb_arn" {
  description = "ARN of the public application load balancer."
  value       = aws_lb.application.arn
}

output "alb_dns_name" {
  description = "AWS DNS name for the public application load balancer."
  value       = aws_lb.application.dns_name
}

output "alb_zone_id" {
  description = "Canonical hosted-zone ID for the application load balancer."
  value       = aws_lb.application.zone_id
}

output "https_listener_arn" {
  description = "HTTPS listener ARN consumed by component routing and operations."
  value       = aws_lb_listener.https.arn
}

output "frontend_target_group_arn" {
  description = "Target group ARN for the frontend ECS service."
  value       = aws_lb_target_group.frontend.arn
}

output "backend_target_group_arn" {
  description = "Target group ARN for the backend ECS service."
  value       = aws_lb_target_group.backend.arn
}
