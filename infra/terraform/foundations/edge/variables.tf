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

variable "application_domain" {
  description = "Fully qualified application domain in the delegated Route 53 hosted zone."
  type        = string
  default     = "happy-post.asksafe.ai"

  validation {
    condition     = var.application_domain == "happy-post.asksafe.ai"
    error_message = "Happy Post uses the delegated happy-post.asksafe.ai application domain."
  }
}

variable "route53_hosted_zone_id" {
  description = "Non-sensitive delegated Route 53 hosted-zone ID."
  type        = string
  default     = "Z07821441TT04VLUXZXPO"

  validation {
    condition     = var.route53_hosted_zone_id == "Z07821441TT04VLUXZXPO"
    error_message = "Happy Post uses the approved delegated Route 53 hosted zone."
  }
}
