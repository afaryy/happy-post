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
