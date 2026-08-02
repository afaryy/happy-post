data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Stack       = "foundation-platform"
  }

  permissions_boundary_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:policy/${local.name_prefix}-permissions-boundary"
  ecs_task_assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowEcsTasksFromThisAccount"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:${data.aws_partition.current.partition}:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        }
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name_prefix}-frontend"
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Expire untagged frontend images after seven days."
      selection = {
        tagStatus   = "untagged"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 7
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Expire untagged backend images after seven days."
      selection = {
        tagStatus   = "untagged"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 7
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/happy-post/frontend"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/happy-post/backend"
  retention_in_days = var.log_retention_in_days
}

resource "aws_iam_role" "frontend_task" {
  name                 = "${local.name_prefix}-frontend-task-role"
  assume_role_policy   = local.ecs_task_assume_role_policy
  permissions_boundary = local.permissions_boundary_arn
}

resource "aws_iam_role" "backend_task" {
  name                 = "${local.name_prefix}-backend-task-role"
  assume_role_policy   = local.ecs_task_assume_role_policy
  permissions_boundary = local.permissions_boundary_arn
}

resource "aws_iam_role" "frontend_execution" {
  name                 = "${local.name_prefix}-frontend-execution-role"
  assume_role_policy   = local.ecs_task_assume_role_policy
  permissions_boundary = local.permissions_boundary_arn
}

resource "aws_iam_role" "backend_execution" {
  name                 = "${local.name_prefix}-backend-execution-role"
  assume_role_policy   = local.ecs_task_assume_role_policy
  permissions_boundary = local.permissions_boundary_arn
}

resource "aws_iam_role_policy" "frontend_execution" {
  name = "${local.name_prefix}-runtime-frontend-execution"
  role = aws_iam_role.frontend_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "GetEcrAuthorizationToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "PullFrontendImage"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = aws_ecr_repository.frontend.arn
      },
      {
        Sid      = "PublishFrontendLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.frontend.arn}:*"
      },
    ]
  })
}

resource "aws_iam_role_policy" "backend_execution" {
  name = "${local.name_prefix}-runtime-backend-execution"
  role = aws_iam_role.backend_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "GetEcrAuthorizationToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "PullBackendImage"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = aws_ecr_repository.backend.arn
      },
      {
        Sid      = "PublishBackendLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.backend.arn}:*"
      },
    ]
  })
}
