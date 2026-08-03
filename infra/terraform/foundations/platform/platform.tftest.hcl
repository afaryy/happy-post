mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "893794041695"
    }
  }

  mock_data "aws_partition" {
    defaults = {
      partition = "aws"
    }
  }
}

run "platform_static_runtime_controls" {
  command = apply

  assert {
    condition     = aws_ecr_repository.frontend.name == "happy-post-sandbox-frontend" && aws_ecr_repository.backend.name == "happy-post-sandbox-backend"
    error_message = "Frontend and backend must use the approved sandbox ECR repository names."
  }

  assert {
    condition     = aws_ecr_repository.frontend.image_tag_mutability == "IMMUTABLE" && aws_ecr_repository.backend.image_tag_mutability == "IMMUTABLE"
    error_message = "Both ECR repositories must enforce immutable image tags."
  }

  assert {
    condition     = aws_ecr_repository.frontend.image_scanning_configuration[0].scan_on_push && aws_ecr_repository.backend.image_scanning_configuration[0].scan_on_push
    error_message = "Both ECR repositories must keep scan-on-push enabled."
  }

  assert {
    condition     = aws_ecs_cluster.this.name == "happy-post-sandbox-cluster" && length([for setting in aws_ecs_cluster.this.setting : setting if setting.name == "containerInsights" && setting.value == "enabled"]) == 1
    error_message = "The platform foundation must create the approved ECS cluster with Container Insights enabled."
  }

  assert {
    condition     = aws_cloudwatch_log_group.frontend.retention_in_days == 14 && aws_cloudwatch_log_group.backend.retention_in_days == 14
    error_message = "Frontend and backend log groups must retain logs for fourteen days in sandbox."
  }

  assert {
    condition     = aws_iam_role.frontend_task.permissions_boundary == "arn:aws:iam::893794041695:policy/happy-post-sandbox-permissions-boundary" && aws_iam_role.backend_task.permissions_boundary == "arn:aws:iam::893794041695:policy/happy-post-sandbox-permissions-boundary"
    error_message = "Runtime task roles must attach the bootstrap-managed permissions boundary."
  }

  assert {
    condition     = aws_iam_role.frontend_execution.permissions_boundary == "arn:aws:iam::893794041695:policy/happy-post-sandbox-permissions-boundary" && aws_iam_role.backend_execution.permissions_boundary == "arn:aws:iam::893794041695:policy/happy-post-sandbox-permissions-boundary"
    error_message = "Runtime execution roles must attach the bootstrap-managed permissions boundary."
  }

  assert {
    condition     = strcontains(aws_iam_role_policy.frontend_execution.policy, "PullFrontendImage") && strcontains(aws_iam_role_policy.frontend_execution.policy, aws_ecr_repository.frontend.arn) && !strcontains(aws_iam_role_policy.frontend_execution.policy, aws_ecr_repository.backend.arn)
    error_message = "The frontend execution policy must pull only the frontend ECR repository."
  }

  assert {
    condition     = strcontains(aws_iam_role_policy.backend_execution.policy, "PullBackendImage") && strcontains(aws_iam_role_policy.backend_execution.policy, aws_ecr_repository.backend.arn) && !strcontains(aws_iam_role_policy.backend_execution.policy, aws_ecr_repository.frontend.arn)
    error_message = "The backend execution policy must pull only the backend ECR repository."
  }
}

run "platform_rejects_non_sandbox_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}
