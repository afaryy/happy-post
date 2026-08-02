variable "aws_region" {
  description = "AWS region for the single Happy Post sandbox environment."
  type        = string
  default     = "ap-southeast-2"

  validation {
    condition     = var.aws_region == "ap-southeast-2"
    error_message = "Happy Post uses ap-southeast-2 for the sandbox environment."
  }
}

variable "project" {
  description = "Project tag and resource-name prefix."
  type        = string
  default     = "happy-post"
}

variable "environment" {
  description = "The only deployment environment."
  type        = string
  default     = "sandbox"

  validation {
    condition     = var.environment == "sandbox"
    error_message = "Happy Post has only the sandbox environment."
  }
}

variable "db_name" {
  description = "Initial PostgreSQL database name."
  type        = string
  default     = "happy_post"
}

variable "master_username" {
  description = "Initial PostgreSQL administrator username."
  type        = string
  default     = "happy_post_admin"
}

variable "aurora_serverless_min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity. Zero permits AWS auto-pause when supported by the selected engine version."
  type        = number
  default     = 0

  validation {
    condition     = var.aurora_serverless_min_capacity >= 0 && var.aurora_serverless_min_capacity <= 4
    error_message = "The sandbox Free Plan capacity guardrail allows a minimum capacity from 0 through 4 ACUs."
  }
}

variable "aurora_serverless_max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity, capped at the current Free Plan guardrail rather than sized from workload metrics."
  type        = number
  default     = 4

  validation {
    condition     = var.aurora_serverless_max_capacity > 0 && var.aurora_serverless_max_capacity <= 4
    error_message = "The sandbox Free Plan capacity guardrail allows a maximum capacity greater than 0 through 4 ACUs."
  }
}
