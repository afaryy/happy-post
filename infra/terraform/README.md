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

`stacks/data` is applied. It reads the network-root state and creates the private
RDS PostgreSQL data boundary:

- a database subnet group using the two existing database subnets;
- a fixed-name Secrets Manager credentials secret with a generated password;
- one private RDS PostgreSQL 16.14 `db.t4g.micro` instance in Single-AZ;
- encrypted gp3 storage (20 GiB allocated and 40 GiB maximum), one-day PITR as
  the active Free Plan maximum, and the documented final-DB-snapshot policy.

The active Free Plan rejects the former seven-day recovery objective. Aurora would
require Express Configuration, which cannot meet Happy Post's private VPC,
backend-only, and Secrets Manager controls. The deployed private RDS instance
uses one-day retention without upgrading the account plan. A future paid
environment must restore a seven-day-or-greater recovery objective.

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
