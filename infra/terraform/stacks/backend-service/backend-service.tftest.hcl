mock_provider "aws" {
  mock_data "aws_iam_role" {
    defaults = {
      name = "happy-post-sandbox-backend-execution-role"
      arn  = "arn:aws:iam::893794041695:role/happy-post-sandbox-backend-execution-role"
    }
  }
}

override_data {
  target = data.terraform_remote_state.network

  values = {
    outputs = {
      application_subnet_ids = {
        "0" = "subnet-0123456789abcdef0"
        "1" = "subnet-0123456789abcdef1"
      }
      security_group_ids = {
        backend = "sg-0123456789abcdef0"
      }
    }
  }
}

override_data {
  target = data.terraform_remote_state.platform

  values = {
    outputs = {
      backend_repository = {
        repository_url = "893794041695.dkr.ecr.ap-southeast-2.amazonaws.com/happy-post-sandbox-backend"
      }
      backend_execution_role_arn = "arn:aws:iam::893794041695:role/happy-post-sandbox-backend-execution-role"
      backend_task_role_arn      = "arn:aws:iam::893794041695:role/happy-post-sandbox-backend-task-role"
      backend_log_group_name     = "/ecs/happy-post/backend"
      ecs_cluster_arn            = "arn:aws:ecs:ap-southeast-2:893794041695:cluster/happy-post-sandbox-cluster"
      ecs_cluster_name           = "happy-post-sandbox-cluster"
    }
  }
}

override_data {
  target = data.terraform_remote_state.data

  values = {
    outputs = {
      database_secret_arn = "arn:aws:secretsmanager:ap-southeast-2:893794041695:secret:happy-post-sandbox-database-credentials"
    }
  }
}

override_data {
  target = data.terraform_remote_state.edge

  values = {
    outputs = {
      backend_target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:893794041695:targetgroup/happy-post-sandbox-backend/0123456789abcdef"
    }
  }
}

run "backend_service_static_deployment_controls" {
  command = apply

  variables {
    backend_image_digest = "sha256:1111111111111111111111111111111111111111111111111111111111111111"
  }

  assert {
    condition     = aws_ecs_task_definition.backend.family == "happy-post-sandbox-backend" && aws_ecs_task_definition.backend.network_mode == "awsvpc" && contains(aws_ecs_task_definition.backend.requires_compatibilities, "FARGATE")
    error_message = "The backend task definition must remain a sandbox Fargate awsvpc task."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.backend.container_definitions)[0].image == "893794041695.dkr.ecr.ap-southeast-2.amazonaws.com/happy-post-sandbox-backend@sha256:1111111111111111111111111111111111111111111111111111111111111111"
    error_message = "The backend task definition must use a digest-pinned ECR image, never a mutable tag."
  }

  assert {
    condition     = jsondecode(aws_ecs_task_definition.backend.container_definitions)[0].secrets[0].name == "DATABASE_URL" && endswith(jsondecode(aws_ecs_task_definition.backend.container_definitions)[0].secrets[0].valueFrom, ":database_url::")
    error_message = "The backend task definition must inject only the database_url key from Secrets Manager."
  }

  assert {
    condition     = aws_ecs_service.backend.desired_count == 1 && aws_ecs_service.backend.network_configuration[0].assign_public_ip == false
    error_message = "The backend ECS service must run privately with one desired sandbox task."
  }

  assert {
    condition     = aws_appautoscaling_target.backend.min_capacity == 1 && aws_appautoscaling_target.backend.max_capacity == 2 && aws_appautoscaling_policy.backend_cpu.target_tracking_scaling_policy_configuration[0].target_value == 65
    error_message = "The backend service must keep the approved one-to-two task CPU target-tracking policy."
  }
}

run "backend_service_rejects_tagged_images" {
  command = plan

  variables {
    backend_image_digest = "latest"
  }

  expect_failures = [
    var.backend_image_digest,
  ]
}
