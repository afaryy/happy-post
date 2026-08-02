terraform {
  required_version = ">= 1.8.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "happy-post-tfstate-893794041695-ap-southeast-2"
    key            = "sandbox/foundations/platform/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "happy-post-sandbox-terraform-lock"
    encrypt        = true
  }
}
