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

variable "vpc_cidr" {
  description = "IPv4 CIDR range for the Happy Post sandbox VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "One public-subnet CIDR for each selected Availability Zone."
  type        = list(string)
  default     = ["10.42.0.0/24", "10.42.1.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) == 2
    error_message = "Provide exactly two public subnet CIDRs."
  }
}

variable "application_subnet_cidrs" {
  description = "One private application-subnet CIDR for each selected Availability Zone."
  type        = list(string)
  default     = ["10.42.16.0/20", "10.42.32.0/20"]

  validation {
    condition     = length(var.application_subnet_cidrs) == 2
    error_message = "Provide exactly two application subnet CIDRs."
  }
}

variable "database_subnet_cidrs" {
  description = "One private database-subnet CIDR for each selected Availability Zone."
  type        = list(string)
  default     = ["10.42.48.0/24", "10.42.49.0/24"]

  validation {
    condition     = length(var.database_subnet_cidrs) == 2
    error_message = "Provide exactly two database subnet CIDRs."
  }
}
