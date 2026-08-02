# Terraform Foundation

This directory contains the Happy Post Terraform roots. Each root has an
independent, DynamoDB-locked state object under the approved `sandbox/` prefix.
CloudFormation, not Terraform, owns the state bucket, lock table, permissions
boundary, and GitHub OIDC operational roles.

## Implemented roots

`foundations/network` creates only the sandbox network baseline:

- one VPC spanning two Availability Zones;
- public, private application, and private database subnets in each zone;
- one Internet Gateway and one public-subnet NAT Gateway;
- public, application, and database route-table boundaries;
- default, ALB, frontend, backend, and database security-group boundaries.

`stacks/data` is implemented but not applied. It reads the network-root state
and creates only the private RDS PostgreSQL data boundary:

- a database subnet group using the two existing database subnets;
- a fixed-name Secrets Manager credentials secret with a generated password;
- a private Single-AZ PostgreSQL 16.14 `db.t4g.micro` instance;
- encrypted gp3 storage (20–40 GiB), seven-day PITR, and the documented final
  snapshot policy.

The implemented roots deliberately do not create ALB, ECS, ECR, ACM, Route 53
records, or CI/CD workload resources.

## State backend

The network root uses this non-secret backend configuration:

| Setting | Value |
| --- | --- |
| Bucket | `happy-post-tfstate-893794041695-ap-southeast-2` |
| Network key | `sandbox/foundations/network/terraform.tfstate` |
| Data key | `sandbox/stacks/data/terraform.tfstate` |
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
terraform -chdir=infra/terraform/stacks/data init -backend=false
terraform -chdir=infra/terraform/stacks/data validate
```

For an authorised read-only review of the real state and AWS configuration, use
the approved short-lived AWS profile and initialise the declared backend:

```bash
terraform -chdir=infra/terraform/foundations/network init
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/foundations/network plan
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/stacks/data plan -lock=false
```

Do not run `terraform apply` locally. Apply remains a future
workflow-dispatch-only GitHub Actions operation using the sandbox OIDC role and
an exact fresh plan for an immutable `main` commit.
