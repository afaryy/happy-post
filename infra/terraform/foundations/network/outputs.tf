output "vpc_id" {
  description = "ID of the Happy Post sandbox VPC."
  value       = aws_vpc.this.id
}

output "availability_zones" {
  description = "The two Availability Zones selected for Happy Post subnets."
  value       = local.selected_azs
}

output "public_subnet_ids" {
  description = "Public subnet IDs for the future internet-facing ALB and NAT Gateway."
  value       = { for key, subnet in aws_subnet.public : key => subnet.id }
}

output "application_subnet_ids" {
  description = "Private application subnet IDs for future ECS services."
  value       = { for key, subnet in aws_subnet.application : key => subnet.id }
}

output "database_subnet_ids" {
  description = "Private database subnet IDs for the mandatory RDS PostgreSQL data stack."
  value       = { for key, subnet in aws_subnet.database : key => subnet.id }
}

output "security_group_ids" {
  description = "Security-group IDs consumed by later ALB, ECS, and RDS stacks."
  value = {
    alb      = aws_security_group.alb.id
    frontend = aws_security_group.frontend.id
    backend  = aws_security_group.backend.id
    database = aws_security_group.database.id
  }
}

output "nat_gateway_id" {
  description = "The single cost-conscious sandbox NAT Gateway."
  value       = aws_nat_gateway.this.id
}
