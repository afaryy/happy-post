# Solution Architecture

Happy Post is a single-environment AWS sandbox with two independently deployable workloads: a Next.js frontend and a FastAPI backend.

## High-Level Solution Architecture

~~~mermaid
flowchart TB
    users[Internet users] --> cloudflare[Cloudflare DNS<br/>asksafe.ai parent zone]
    cloudflare -->|delegates happy-post.asksafe.ai| route53[Route 53 public hosted zone]
    route53 -->|A/AAAA alias resolution| alb[Internet-facing ALB<br/>HTTPS :443]
    acm[ACM public certificate] -. "TLS certificate" .-> alb
    alb -->|default /* and /frontend/*| frontend_tg[Frontend target group]
    alb -->|higher-priority /api/* and /backend/*| backend_tg[Backend target group]
    frontend_tg --> frontend[Frontend ECS Fargate service<br/>Next.js]
    backend_tg --> backend[Backend ECS Fargate service<br/>FastAPI]
    backend -->|PostgreSQL 5432 only| rds[Private RDS PostgreSQL]
    frontend --> frontend_logs[CloudWatch Logs]
    backend --> backend_logs[CloudWatch Logs]
~~~

Source: [solution-architecture.mmd](diagrams/solution-architecture.mmd).

Cloudflare remains the parent DNS provider for asksafe.ai and delegates happy-post.asksafe.ai to Route 53. Route 53 resolves the application domain to the public ALB; ACM terminates HTTPS at the ALB.

## AWS Sandbox Network and Runtime

![AWS sandbox runtime architecture](diagrams/aws-ecs-runtime-architecture.drawio.svg)

The frontend and backend are independently versioned ECS Fargate services behind a shared HTTPS Application Load Balancer. Path-based routing sends `/*` traffic to the Next.js frontend and `/api/*` traffic to the FastAPI backend. Happy Post is a bedtime MVP that asks each signed-in user to record at least three small happy things; the backend persists those user-scoped daily entries in PostgreSQL through `DATABASE_URL`. The application schema keeps users in `users`, opaque session-token hashes in `user_sessions`, one row per user and date in `daily_entries`, and one row per happy item in `daily_entry_items`, so the UI can start with three prompts while still allowing additional happy things. Only the backend security group can connect to the private RDS PostgreSQL instance on TCP 5432. The backend task definition injects only the `database_url` key from Secrets Manager through the backend task execution role. Both services use separate ECR repositories, task-definition families, target groups, log groups, and deployment histories while sharing the ECS cluster, VPC, ALB, and application domain.

Both services have been deployed through the controlled ECS deployment workflow. Backend public smoke tests pass at `/backend/healthz` and `/backend/version`; frontend public smoke tests pass at `/healthz` and `/version`. The backend version endpoint reports the deployed immutable image digest, while the frontend version endpoint currently reports the application version `0.1.0`.

The runtime diagram deliberately separates deployed traffic and network controls from provisioning and CI/CD. Amazon ECR, Secrets Manager, CloudWatch, Route 53, and ACM are regional managed services outside the VPC. RDS is private in database subnets; Secrets Manager is not placed in a database subnet.

## Delivery and Control Plane

![AWS delivery and control-plane architecture](diagrams/delivery-and-control-plane.drawio.svg)

CloudFormation bootstrap creates the private versioned S3 Terraform state bucket, DynamoDB lock table, runtime permissions boundary, and distinct GitHub Actions roles while reusing the existing account-level GitHub OIDC provider. GitHub Actions uses separate Terraform plan, Terraform apply, ECR publish, and ECS deployment roles. The independent platform root defines the two private ECR repositories, ECS cluster, component log groups, and four runtime roles; it does not create a task definition or service. ECR uses immutable tags, scan-on-push, and seven-day cleanup of untagged images. Frontend and backend images are built, scanned, published, deployed, and rolled back independently.

## DNS and TLS Boundary

| Configuration | Value |
| --- | --- |
| Route 53 hosted zone | happy-post.asksafe.ai |
| Hosted-zone ID | Z07821441TT04VLUXZXPO |
| Application domain | happy-post.asksafe.ai |

The hosted-zone ID is non-sensitive configuration. The applied edge root manages ACM DNS-validation and application records only inside the delegated Route 53 zone; it never manages Cloudflare parent-zone delegation. It creates a port 80 listener that redirects to HTTPS and a port 443 listener with the ACM certificate. TLS terminates at the ALB. ALB-to-task traffic is HTTP; end-to-end TLS is deferred. API Gateway and CloudFront are not baseline components.

## Network Egress

Sandbox uses one NAT Gateway in a public subnet as an explicit cost/availability trade-off. Private application subnets use it for outbound ECR, CloudWatch Logs, and approved external-dependency access. The Internet Gateway supports the public ALB and NAT Gateway only. RDS has no public route. VPC endpoints remain disabled.

## Routing

| ALB path | Target |
| --- | --- |
| /* | Frontend ECS service |
| /api/* | Backend ECS service |
| /frontend/healthz, /frontend/version | Frontend ECS service |
| /backend/healthz, /backend/version | Backend ECS service |

Each service must expose container-local `/healthz` and `/version`, plus its public component aliases listed above. ALB does not rewrite request paths. Listener priority is: `/api/*`, backend validation aliases, frontend validation aliases, then `/*` as the default frontend rule.

## ECS Service Scaling

Each deployed ECS service uses CPU target-tracking scaling: minimum one task, maximum two tasks, a 65% CPU target, a 60-second scale-out cooldown, and a 300-second scale-in cooldown. This is intentionally modest for sandbox cost control. Fargate supplies compute capacity, so no ECS cluster auto-scaling configuration is required.

## CI/CD Delivery Architecture

~~~mermaid
flowchart TB
    pr[Pull request] --> checks[Tests, linting, Snyk, SonarQube, Trivy,<br/>Terraform format, validate, and TFLint]
    checks --> merge[Protected merge to main]
    merge --> scope{Changed scope}
    scope -->|Application| build[Build, Trivy scan, and push<br/>changed immutable image digest]
    build --> handoff[Seven-day digest-handoff artifact]
    handoff --> bootstrap[Manual component-selected<br/>initial-service bootstrap]
    bootstrap --> initial[Create selected initial ECS service]
    handoff --> deploy[Manual component-selected<br/>ECS deployment]
    deploy --> verify[Wait for ECS and ALB health<br/>then run HTTPS smoke test]
    verify --> rollback[Manual component-selected<br/>known-good rollback]
    manual_plan[Manual Terraform plan<br/>select target] --> fresh_plan[Workflow dispatch resolves immutable main commit]
    fresh_plan --> tf_sandbox[GitHub environment: sandbox]
    tf_sandbox --> apply[Apply that exact plan]
~~~

The sandbox environment is an OIDC/configuration boundary, not an approval gate: it has no required reviewers. Pull requests run backend-free Terraform validation only and never receive AWS credentials. Terraform plan, apply, and destroy are workflow-dispatch-only operations: each resolves and logs the immutable `main` SHA and accepts only a fixed canonical-root target. Plan uses the read-only plan role; apply creates a fresh plan for that checkout and applies that exact plan through the separate apply role. Initial service bootstrap verifies an ECR digest then applies only the selected service root. Subsequent deployment and rollback workflows use the distinct ECS deployment role to update only one existing service. Merge never applies Terraform. Detailed sources are [CI/CD diagram](diagrams/cicd.mmd) and [Terraform diagram](diagrams/terraform.mmd).

## Terraform and Deployment Ownership

~~~mermaid
flowchart TB
    oidc[Existing GitHub OIDC provider] --> bootstrap[CloudFormation bootstrap]
    bootstrap --> state[S3 Terraform state bucket<br/>private and versioned]
    bootstrap --> lock[DynamoDB Terraform state lock table]
    bootstrap --> roles[Separate GitHub OIDC roles<br/>sandbox plan; sandbox apply/destroy; sandbox ECS deploy]

    state --> root[Terraform root configuration]
    lock --> root
    roles --> root
    root --> foundations[Foundations]
    root --> workloads[Workload stacks]

    subgraph foundations
        network[network<br/>VPC, subnets, routes, IGW, NAT]
        identity[security-identity<br/>IAM, security groups, Secrets Manager]
        platform[platform<br/>ECR, ECS cluster, ALB]
        scaling[ECS service scaling<br/>CPU target tracking: 1–2 tasks, 65%]
        edge[edge<br/>Route 53 records and ACM]
    end

    subgraph workloads
        data[data<br/>RDS PostgreSQL and backups]
        backend[backend-service<br/>task definition and ECS service]
        frontend[frontend-service<br/>task definition and ECS service]
        observability[observability<br/>CloudWatch log groups and alarms]
    end

    network --> identity
    identity --> platform
    platform --> edge
    platform --> scaling
    network --> data
    identity --> data
    platform --> backend
    scaling --> backend
    edge --> backend
    data --> backend
    platform --> frontend
    scaling --> frontend
    edge --> frontend
    edge --> observability
    backend --> observability
    frontend --> observability
~~~

Source: [terraform.mmd](diagrams/terraform.mmd).

Terraform owns foundations and stable configuration: networking, private RDS PostgreSQL and database subnets/security group, Secrets Manager database credentials, ECR, ECS cluster, runtime IAM roles, logging, ALB/listeners, Route 53 and ACM records, ECS services, and initial task definitions. The mandatory data stack has its own state and lifecycle.

CloudFormation bootstrap owns the S3 state bucket, DynamoDB lock table, runtime permissions boundary, and GitHub OIDC roles. Terraform uses the S3 backend with DynamoDB as the only locking mechanism. The version-controlled bootstrap source is [`infra/bootstrap/happy-post-terraform-bootstrap.yaml`](../infra/bootstrap/happy-post-terraform-bootstrap.yaml). The state bucket is retained; the lock table has deletion protection and is retained on bootstrap stack deletion or replacement.

The version-controlled [`foundations/network`](../infra/terraform/foundations/network) root declares the applied two-AZ VPC, public/application/database subnet tiers, one NAT Gateway, route tables, and ALB/frontend/backend/database security-group boundaries. The separate [`stacks/data`](../infra/terraform/stacks/data) root reads only its network outputs and has its own `sandbox/stacks/data/terraform.tfstate` object. It has applied the private DB subnet group, fixed-name database credentials secret, and private RDS PostgreSQL instance. The applied [`foundations/platform`](../infra/terraform/foundations/platform) root owns ECR, the cluster, log groups, and runtime roles; the applied [`foundations/edge`](../infra/terraform/foundations/edge) root consumes network state and owns ACM, ALB, and delegated-zone records. The applied independent [`stacks/backend-service`](../infra/terraform/stacks/backend-service) and [`stacks/frontend-service`](../infra/terraform/stacks/frontend-service) roots consume their required remote-state outputs and created the initial digest-pinned services. The bootstrap workflow is initial-creation-only. Later delivery registers a digest-pinned task-definition revision and updates only the selected existing service through the ECS deployment role. The P6 application code keeps the existing `0001_create_posts` migration and adds append-only `0002_create_users_daily_entries`, which replaces the temporary `posts` table with `users`, `user_sessions`, `daily_entries`, and `daily_entry_items`; deployment must run the migration before the backend image that requires it.

## Bootstrap Inputs

| Input | Approved value |
| --- | --- |
| State bucket name | `happy-post-tfstate-893794041695-ap-southeast-2` |
| State-key prefix | `sandbox/` |
| DynamoDB lock table | `happy-post-sandbox-terraform-lock` |
| Route 53 hosted-zone ID | `Z07821441TT04VLUXZXPO` |

CloudFormation created the state bucket and lock table. The lock table must not be removed during normal bootstrap teardown: first remove dependent Terraform state safely, disable DynamoDB deletion protection through an approved operation, then explicitly remove the retained table only if teardown is required.

An ECR push does not update ECS by itself. The manual service-bootstrap workflow verifies a supplied immutable digest and uses Terraform to create one selected initial service. The manual ECS deployment workflow verifies the same digest/source-commit provenance, registers a digest-pinned task-definition revision, updates only the selected existing service, and records known-good revisions for component-scoped rollback. Terraform ignores subsequent service task-definition drift so that it does not undo a valid deployment.

## Deployed RDS PostgreSQL Sandbox Configuration

| Setting | Value |
| --- | --- |
| Engine | RDS PostgreSQL 16.14 at creation; automatic minor-version upgrades enabled |
| Runtime | One private `db.t4g.micro` instance; Single-AZ |
| Storage | Encrypted gp3; 20 GiB allocated with autoscaling capped at 40 GiB |
| Recovery | One-day PITR, the maximum permitted by the active Free Plan; backup 15:30-16:00 UTC daily |
| Maintenance | sun:16:30-sun:17:00 UTC |
| Credentials | Generated by Terraform and stored only in `happy-post-sandbox-database-credentials`; secret value is never an output |
| Destroy | Deletion protection disabled; final snapshot required with a stable random suffix; automated backups are not retained |

See [Operations](operations.md) for the required restore-test procedure.

### Free Plan design decision

The active AWS Free Plan rejected the former seven-day recovery objective. It also
requires Aurora to use Express Configuration, which cannot meet this solution's
private VPC, backend-only security-group, and Secrets Manager credential design.
The deployed RDS PostgreSQL `db.t4g.micro` configuration with one-day PITR
preserves those required controls without changing the account plan. A future paid
environment must restore a seven-day-or-greater recovery objective.

## Explicitly Outside the Baseline

WAF, ECS Service Connect, ECS blue/green deployment, VPC endpoints, deployment notifications, customer-managed KMS, and end-to-end TLS are disabled by default. Each needs separate approval and documentation before adoption.
