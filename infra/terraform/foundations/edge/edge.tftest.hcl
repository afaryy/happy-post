mock_provider "aws" {}

override_data {
  target = data.terraform_remote_state.network

  values = {
    outputs = {
      vpc_id = "vpc-0123456789abcdef0"
      public_subnet_ids = {
        "0" = "subnet-0123456789abcdef0"
        "1" = "subnet-0123456789abcdef1"
      }
      security_group_ids = {
        alb = "sg-0123456789abcdef0"
      }
    }
  }
}

run "edge_rejects_non_sandbox_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}

run "edge_rejects_unapproved_application_domain" {
  command = plan

  variables {
    application_domain = "example.com"
  }

  expect_failures = [
    var.application_domain,
  ]
}

run "edge_rejects_unapproved_hosted_zone_id" {
  command = plan

  variables {
    route53_hosted_zone_id = "Z11111111111111111111"
  }

  expect_failures = [
    var.route53_hosted_zone_id,
  ]
}
