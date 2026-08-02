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

variable "log_retention_in_days" {
  description = "CloudWatch Logs retention for each ECS component in the cost-conscious sandbox."
  type        = number
  default     = 14

  validation {
    condition     = var.log_retention_in_days == 14
    error_message = "Happy Post uses fourteen-day component log retention in sandbox."
  }
}
