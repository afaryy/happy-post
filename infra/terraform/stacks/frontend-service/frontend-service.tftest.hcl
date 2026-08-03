mock_provider "aws" {}

override_data {
  target = data.terraform_remote_state.network

  values = {
    outputs = {
      application_subnet_ids = {
        "0" = "subnet-0123456789abcdef0"
        "1" = "subnet-0123456789abcdef1"
      }
      security_group_ids = {
        frontend = "sg-0123456789abcdef0"
      }
    }
  }
}

override_data {
  target = data.terraform_remote_state.platform

  values = {
    outputs = {
      frontend_repository = {
        repository_url = "893794041695.dkr.ecr.ap-southeast-2.amazonaws.com/happy-post-sandbox-frontend"
      }
      frontend_execution_role_arn = "arn:aws:iam::893794041695:role/happy-post-sandbox-frontend-execution-role"
      frontend_task_role_arn      = "arn:aws:iam::893794041695:role/happy-post-sandbox-frontend-task-role"
      frontend_log_group_name     = "/ecs/happy-post/frontend"
      ecs_cluster_arn             = "arn:aws:ecs:ap-southeast-2:893794041695:cluster/happy-post-sandbox-cluster"
      ecs_cluster_name            = "happy-post-sandbox-cluster"
    }
  }
}

override_data {
  target = data.terraform_remote_state.edge

  values = {
    outputs = {
      frontend_target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:893794041695:targetgroup/happy-post-sandbox-frontend/0123456789abcdef"
    }
  }
}

run "frontend_service_static_deployment_controls" {
  command = apply

  variables {
    frontend_image_digest = "sha256:2222222222222222222222222222222222222222222222222222222222222222"
  }

  assert {
    condition     = aws_ecs_task_definition.frontend.family == "happy-post-sandbox-frontend" && aws_ecs_task_definition.frontend.network_mode == "awsvpc" && contains(aws_ecs_task_definition.frontend.requires_compatibilities, "FARGATE")
    error_message = "The frontend task definition must remain a sandbox Fargate awsvpc task."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.frontend.container_definitions)[0].image == "893794041695.dkr.ecr.ap-southeast-2.amazonaws.com/happy-post-sandbox-frontend@sha256:2222222222222222222222222222222222222222222222222222222222222222"
    error_message = "The frontend task definition must use a digest-pinned ECR image, never a mutable tag."
  }

  assert {
    condition     = !can(jsondecode(aws_ecs_task_definition.frontend.container_definitions)[0].secrets)
    error_message = "The frontend task definition must not receive Secrets Manager values."
  }

  assert {
    condition     = aws_ecs_service.frontend.desired_count == 1 && aws_ecs_service.frontend.network_configuration[0].assign_public_ip == false
    error_message = "The frontend ECS service must run privately with one desired sandbox task."
  }

  assert {
    condition     = aws_appautoscaling_target.frontend.min_capacity == 1 && aws_appautoscaling_target.frontend.max_capacity == 2 && aws_appautoscaling_policy.frontend_cpu.target_tracking_scaling_policy_configuration[0].target_value == 65
    error_message = "The frontend service must keep the approved one-to-two task CPU target-tracking policy."
  }
}

run "frontend_service_rejects_tagged_images" {
  command = plan

  variables {
    frontend_image_digest = "latest"
  }

  expect_failures = [
    var.frontend_image_digest,
  ]
}
