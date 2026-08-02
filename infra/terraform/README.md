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

`foundations/platform` is applied. It is deliberately independent of network and
data state because ECR repositories, the ECS cluster,
component log groups, and runtime IAM roles have no VPC or database dependency.
It creates two private scan-on-push, immutable ECR repositories; one ECS cluster
with Container Insights enabled; fourteen-day frontend and backend log groups;
and separate frontend/backend task and execution roles. Task roles have no
application AWS API permissions. Each execution role can pull only its own image
and publish only to its own log group. The backend execution role receives named
database-secret access only in the later backend service stack that injects it.
The current lifecycle policies expire only untagged images after seven days. Do
not add tagged-image retention until the image-publication workflow defines a
protected immutable tag contract that retains the current and previous deployable
digests for rollback.

`foundations/edge` is applied. It reads only network state and
creates the ACM certificate and DNS validation records inside the delegated Route
53 zone, the public ALB, port 80 to 443 redirect, port 443 listener, target
groups, deterministic route rules, and the Route 53 A alias. The required
network HTTP ingress reconciliation is applied.

`stacks/backend-service` and `stacks/frontend-service` are defined but not
applied. Each reads its specific network, platform, and edge state; the backend
also reads the data secret ARN. Each requires a real, scanned SHA-256 ECR digest
as a non-default input. They create the initial Fargate task definition and
service, deployment circuit breaker, target attachment, and one-to-two-task CPU
target tracking. The backend root grants only its execution role
`secretsmanager:GetSecretValue` for the fixed database secret and injects only
the secret's `database_url` JSON key as `DATABASE_URL`. Do not apply either root
until the image-publication process supplies a real digest. Use the manual
`Bootstrap ECS Service` workflow with the matching seven-day digest-handoff
artifact; it validates the digest and verifies that it belongs to the selected
repository before applying only the matching service root.

## State backend

The network root uses this non-secret backend configuration:

| Setting | Value |
| --- | --- |
| Bucket | `happy-post-tfstate-893794041695-ap-southeast-2` |
| Network key | `sandbox/foundations/network/terraform.tfstate` |
| Data key | `sandbox/stacks/data/terraform.tfstate` |
| Platform key | `sandbox/foundations/platform/terraform.tfstate` |
| Edge key | `sandbox/foundations/edge/terraform.tfstate` |
| Backend service key | `sandbox/stacks/backend-service/terraform.tfstate` |
| Frontend service key | `sandbox/stacks/frontend-service/terraform.tfstate` |
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
terraform -chdir=infra/terraform/foundations/platform init -backend=false
terraform -chdir=infra/terraform/foundations/platform validate
terraform -chdir=infra/terraform/foundations/edge init -backend=false
terraform -chdir=infra/terraform/foundations/edge validate
terraform -chdir=infra/terraform/stacks/backend-service init -backend=false
terraform -chdir=infra/terraform/stacks/backend-service validate
terraform -chdir=infra/terraform/stacks/frontend-service init -backend=false
terraform -chdir=infra/terraform/stacks/frontend-service validate
```

For an authorised read-only review of the real state and AWS configuration, use
the approved short-lived AWS profile and initialise the declared backend:

```bash
terraform -chdir=infra/terraform/foundations/network init
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/foundations/network plan
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/stacks/data plan -lock=false
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/foundations/platform plan -lock=false
AWS_PROFILE=happy-post-sandbox terraform -chdir=infra/terraform/foundations/edge plan -lock=false
```

Do not run `terraform apply` locally. Apply remains a future
workflow-dispatch-only GitHub Actions operation using the sandbox OIDC role and
an exact fresh plan for an immutable `main` commit. The service roots need real
scanned image digests; their example values are intentionally non-deployable.
