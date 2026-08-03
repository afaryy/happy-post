mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = [
        "ap-southeast-2a",
        "ap-southeast-2b",
        "ap-southeast-2c",
      ]
    }
  }
}

run "network_static_security_boundaries" {
  command = apply

  assert {
    condition     = aws_vpc.this.cidr_block == "10.42.0.0/16"
    error_message = "The sandbox VPC must keep the approved 10.42.0.0/16 CIDR."
  }

  assert {
    condition     = aws_vpc.this.enable_dns_hostnames && aws_vpc.this.enable_dns_support
    error_message = "The sandbox VPC must support DNS for ECS, ALB, and RDS integration."
  }

  assert {
    condition     = length(aws_subnet.public) == 2 && length(aws_subnet.application) == 2 && length(aws_subnet.database) == 2
    error_message = "Public, private application, and private database subnet tiers must each span two Availability Zones."
  }

  assert {
    condition     = aws_subnet.public["0"].map_public_ip_on_launch == false && aws_subnet.public["1"].map_public_ip_on_launch == false
    error_message = "Public subnets must not auto-assign public IPs to launched resources."
  }

  assert {
    condition     = length([for route in aws_route_table.application.route : route if route.cidr_block == "0.0.0.0/0" && route.nat_gateway_id == aws_nat_gateway.this.id]) == 1
    error_message = "Private application subnets must use the single sandbox NAT Gateway for outbound access."
  }

  assert {
    condition     = length(aws_route_table.database.route) == 0
    error_message = "Private database subnets must not have internet or NAT routes."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.alb_https.from_port == 443 && aws_vpc_security_group_ingress_rule.alb_https.cidr_ipv4 == "0.0.0.0/0"
    error_message = "The ALB security group must allow public HTTPS ingress."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.alb_http.from_port == 80 && aws_vpc_security_group_ingress_rule.alb_http.cidr_ipv4 == "0.0.0.0/0"
    error_message = "The ALB security group must allow public HTTP ingress only for HTTP-to-HTTPS redirect."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.backend_from_alb.referenced_security_group_id == aws_security_group.alb.id && aws_vpc_security_group_ingress_rule.backend_from_alb.from_port == 8000
    error_message = "Backend service ingress must come only from the ALB security group on the backend container port."
  }

  assert {
    condition     = aws_vpc_security_group_egress_rule.backend_database.referenced_security_group_id == aws_security_group.database.id && aws_vpc_security_group_egress_rule.backend_database.from_port == 5432
    error_message = "Backend egress to PostgreSQL must target only the database security group on TCP 5432."
  }
}

run "network_rejects_non_sandbox_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}
