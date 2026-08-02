data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/foundations/network/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}

data "terraform_remote_state" "platform" {
  backend = "s3"

  config = {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/foundations/platform/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}

data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/stacks/data/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}

data "terraform_remote_state" "edge" {
  backend = "s3"

  config = {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/foundations/edge/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
    Stack       = "stack-backend-service"
  }
  backend_image = "${data.terraform_remote_state.platform.outputs.backend_repository.repository_url}@${var.backend_image_digest}"
}

data "aws_iam_role" "backend_execution" {
  name = element(split("/", data.terraform_remote_state.platform.outputs.backend_execution_role_arn), 1)
}

resource "aws_iam_role_policy" "database_secret_injection" {
  name = "${local.name_prefix}-runtime-backend-secret-injection"
  role = data.aws_iam_role.backend_execution.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "ReadNamedDatabaseSecretAtTaskLaunch"
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = data.terraform_remote_state.data.outputs.database_secret_arn
    }]
  })
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.terraform_remote_state.platform.outputs.backend_execution_role_arn
  task_role_arn            = data.terraform_remote_state.platform.outputs.backend_task_role_arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = local.backend_image
    essential = true
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
      appProtocol   = "http"
    }]
    environment = [{
      name  = "APP_VERSION"
      value = var.backend_image_digest
    }]
    secrets = [{
      name      = "DATABASE_URL"
      valueFrom = "${data.terraform_remote_state.data.outputs.database_secret_arn}:database_url::"
    }]
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = data.terraform_remote_state.platform.outputs.backend_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
        "mode"                  = "blocking"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name                               = "${local.name_prefix}-backend"
  cluster                            = data.terraform_remote_state.platform.outputs.ecs_cluster_arn
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = 1
  launch_type                        = "FARGATE"
  platform_version                   = "LATEST"
  health_check_grace_period_seconds  = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    assign_public_ip = false
    security_groups  = [data.terraform_remote_state.network.outputs.security_group_ids.backend]
    subnets          = values(data.terraform_remote_state.network.outputs.application_subnet_ids)
  }

  load_balancer {
    container_name   = "backend"
    container_port   = 8000
    target_group_arn = data.terraform_remote_state.edge.outputs.backend_target_group_arn
  }

  depends_on = [aws_iam_role_policy.database_secret_injection]

  lifecycle {
    ignore_changes = [task_definition]
  }
}

resource "aws_appautoscaling_target" "backend" {
  max_capacity       = 2
  min_capacity       = 1
  resource_id        = "service/${data.terraform_remote_state.platform.outputs.ecs_cluster_name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${local.name_prefix}-backend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 65
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
