# CI/CD and Control Plane

![AWS delivery and control-plane architecture](diagrams/delivery-and-control-plane.drawio.svg)

CloudFormation bootstrap owns the Terraform S3 state bucket, DynamoDB lock table, runtime permissions boundary, and GitHub Actions IAM roles. It reuses the existing GitHub OIDC provider; neither Terraform nor CloudFormation creates that account-level provider.

Terraform state is private and versioned in S3 under `sandbox/`, with DynamoDB as the only locking mechanism. Same-repository pull-request plans use the `pull_request` OIDC subject. Terraform apply/destroy and ECS deploy use the `sandbox` GitHub environment as an OIDC/configuration boundary without required reviewers. ECR publication uses the `main` branch OIDC subject.

Terraform apply is workflow-dispatch only: it takes a selected immutable `main` commit, creates a fresh plan, and applies that exact plan. A merge never applies Terraform. Destroy is a separate workflow-dispatch operation with explicit confirmation.

The future workflow set is intentionally separate: `terraform-test.yml`, `terraform-plan.yml`, `terraform-apply.yml`, and `terraform-destroy.yml`. They have different triggers and IAM permissions; no reusable `_terraform-operation.yml` workflow or composite Terraform-init action is part of the baseline.

Frontend and backend delivery are independent. A changed service image is built, scanned, pushed by immutable digest to its own ECR repository, registered as a new task-definition revision, and deployed only to its matching ECS service. ECS rolling deployment, the deployment circuit breaker, stability checks, and smoke tests provide the baseline rollout. Rollback selects the previous known-good task-definition revision and immutable digest. Native ECS blue/green deployment is deferred.
