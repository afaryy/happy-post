# Terraform Foundation

This directory contains the Happy Post Terraform roots. Each root has an
independent, DynamoDB-locked state object under the approved `sandbox/` prefix.
CloudFormation, not Terraform, owns the state bucket, lock table, permissions
boundary, and GitHub OIDC operational roles.

## Implemented root

`foundations/network` creates only the sandbox network baseline:

- one VPC spanning two Availability Zones;
- public, private application, and private database subnets in each zone;
- one Internet Gateway and one public-subnet NAT Gateway;
- public, application, and database route-table boundaries;
- default, ALB, frontend, backend, and database security-group boundaries.

It deliberately does not create ALB, ECS, ECR, ACM, Route 53 records, RDS,
Secrets Manager, or CI/CD resources.

## State backend

The network root uses this non-secret backend configuration:

| Setting | Value |
| --- | --- |
| Bucket | `happy-post-tfstate-893794041695-ap-southeast-2` |
| Key | `sandbox/foundations/network/terraform.tfstate` |
| Region | `ap-southeast-2` |
| Lock table | `happy-post-sandbox-terraform-lock` |

Do not create or delete these backend resources from Terraform. They are
CloudFormation bootstrap resources and the lock table is deletion-protected.

## Local validation

From the repository root, run backend-free validation first:

```bash
terraform -chdir=infra/terraform/foundations/network init -backend=false
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/foundations/network validate
```

For an authorised read-only review of the real state and AWS configuration, use
the approved short-lived AWS profile and initialise the declared backend:

```bash
terraform -chdir=infra/terraform/foundations/network init
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/foundations/network plan
```

Do not run `terraform apply` locally. Apply remains a future
workflow-dispatch-only GitHub Actions operation using the sandbox OIDC role and
an exact fresh plan for an immutable `main` commit.
