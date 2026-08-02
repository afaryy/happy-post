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
    Stack       = "stack-frontend-service"
  }
  frontend_image = "${data.terraform_remote_state.platform.outputs.frontend_repository.repository_url}@${var.frontend_image_digest}"
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.terraform_remote_state.platform.outputs.frontend_execution_role_arn
  task_role_arn            = data.terraform_remote_state.platform.outputs.frontend_task_role_arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = local.frontend_image
    essential = true
    portMappings = [{
      containerPort = 3000
      hostPort      = 3000
      protocol      = "tcp"
      appProtocol   = "http"
    }]
    environment = [{
      name  = "APP_VERSION"
      value = var.frontend_image_digest
    }]
    healthCheck = {
      command     = ["CMD-SHELL", "wget -q -O /dev/null http://localhost:3000/healthz || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = data.terraform_remote_state.platform.outputs.frontend_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "frontend"
        "awslogs-create-group"  = "false"
        "mode"                  = "blocking"
      }
    }
  }])
}

resource "aws_ecs_service" "frontend" {
  name                               = "${local.name_prefix}-frontend"
  cluster                            = data.terraform_remote_state.platform.outputs.ecs_cluster_arn
  task_definition                    = aws_ecs_task_definition.frontend.arn
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
    security_groups  = [data.terraform_remote_state.network.outputs.security_group_ids.frontend]
    subnets          = values(data.terraform_remote_state.network.outputs.application_subnet_ids)
  }

  load_balancer {
    container_name   = "frontend"
    container_port   = 3000
    target_group_arn = data.terraform_remote_state.edge.outputs.frontend_target_group_arn
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}

resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = 2
  min_capacity       = 1
  resource_id        = "service/${data.terraform_remote_state.platform.outputs.ecs_cluster_name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${local.name_prefix}-frontend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 65
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
