# Happy Post

Happy Post is a cloud-native application with a Next.js frontend and FastAPI backend. The delivery architecture uses two independently deployable container images and ECS Fargate services.

## Current status

The MVP application source is present: a FastAPI daily-entry API and a warm Next.js bedtime page where each signed-in user records at least three small happy things, with optional extra happy items when they have more to save. Local containerisation runs frontend, backend, and local PostgreSQL together through Docker Compose. P4's Terraform network, private RDS PostgreSQL data, ECR/ECS platform, edge, and both digest-pinned ECS service roots are applied. Terraform, application, security, image-publication, initial-service bootstrap, post-bootstrap deployment, and rollback workflows are implemented. The deployed frontend and backend services have been updated through the controlled ECS deployment workflow and their public HTTPS smoke tests pass.

- [Backend MVP](backend/README.md): email/password MVP auth, user-scoped daily-entry API, operational endpoints, PostgreSQL persistence, Alembic migration, tests, linting, and local configuration example.
- [Frontend MVP](frontend/README.md): sign-in/sign-up UI, three-small-happy-things bedtime UI, private history calendar, backend API integration, operational endpoints, tests, linting, and local configuration example.
- [Terraform foundation](infra/terraform/README.md): version constraints, remote state, and applied sandbox network, RDS data, ECR/ECS platform, edge, and service roots.
- [Terraform workflow controls](.github/workflows/terraform-test.yml): backend-free PR format, validate, native test, and TFLint checks plus manual target-selected plan, apply, and destroy controls.
- [Application CI](.github/workflows/application-ci.yml): changed-component backend and frontend linting, unit tests, and frontend build checks.
- [Image publication](.github/workflows/image-publish.yml): changed-component `main` publication plus a main-only manual initial publication, Trivy gate, immutable ECR publication, and digest handoff artifact.
- [Service bootstrap](.github/workflows/service-bootstrap.yml): manually creates one selected initial service only after repository-specific digest and immutable source-commit-tag verification.
- [Database migration](.github/workflows/database-migration.yml): manually runs `alembic upgrade head` as a one-off private ECS Fargate task from a verified backend image digest before deploying a backend release that requires schema changes.
- [ECS deployment](.github/workflows/ecs-deploy.yml): manually updates one existing service with a verified immutable digest, then verifies ECS, ALB, and public HTTPS health.
- [ECS rollback](.github/workflows/ecs-rollback.yml): manually restores one existing service to its immediately preceding known-good task-definition revision.

## Deployed service verification

The controlled ECS deployment workflow has successfully deployed both services. Backend smoke tests passed at `/backend/healthz` and `/backend/version`; the backend version response reports the deployed immutable image digest. Frontend smoke tests passed at `/healthz` and `/version`; the frontend version response currently reports the application version `0.1.0`. The rollback workflow is available for component-scoped recovery and should be rehearsed only if time permits before assessment submission.

Database-changing releases require one extra controlled step before the backend deployment. After publishing the backend image from `main`, run the manual database migration workflow with the same backend `image_digest` and `source_commit`, confirm `migrate-backend`, verify success, and only then run the backend ECS deployment workflow with that digest. After this workflow is merged, update the `happy-post-sandbox-bootstrap` CloudFormation stack before running it so the deployment role has the scoped `ecs:RunTask` permission for migration tasks.

## Run locally with containers

Docker Compose defines `db`, `backend-migrate`, `backend`, and `frontend` for a
local PostgreSQL-backed run. From the repository root, run:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

The frontend is available at `http://127.0.0.1:3000`; its relative `/api/entries/*`
requests are forwarded internally to `http://backend:8000`. The backend is available
at `http://127.0.0.1:8000` by default. Local PostgreSQL binds to
`127.0.0.1:5432` by default. If port 8000 or 5432 is temporarily in use, change
only the non-sensitive host-side bindings:

```bash
HAPPY_POST_BACKEND_HOST_PORT=18000 HAPPY_POST_DB_HOST_PORT=15432 docker compose up --build -d
HAPPY_POST_BACKEND_HOST_PORT=18000 HAPPY_POST_DB_HOST_PORT=15432 docker compose ps
HAPPY_POST_BACKEND_HOST_PORT=18000 HAPPY_POST_DB_HOST_PORT=15432 docker compose down --remove-orphans
```

This keeps internal frontend routing on `backend:8000` and internal database
access on `db:5432`. Host ports bind only to loopback. The images run as non-root
users and contain no AWS secrets. Local Compose database credentials and session
secret are development-only defaults and must not be reused for AWS or real
users.

## Canonical baseline

- AWS environment and GitHub environment: `sandbox`
- Parent DNS: Cloudflare manages `asksafe.ai`
- Route 53 hosted zone: `happy-post.asksafe.ai`
- Application domain: `happy-post.asksafe.ai`
- Route 53 hosted-zone ID: `Z07821441TT04VLUXZXPO` (non-sensitive configuration)
- Delivery model: two images, two ECS services, one ECS cluster, and one HTTPS ALB
- Database: deployed private RDS PostgreSQL 16.14 instance, accessed by the backend only
- Database recovery: automated backups and point-in-time recovery with one-day retention, the maximum permitted by the active AWS Free Plan
- Database sandbox configuration: `db.t4g.micro`, Single-AZ, encrypted gp3 storage (20 GiB allocated; 40 GiB maximum); this is a cost-conscious sandbox configuration, not production sizing guidance.
- Terraform state: private versioned S3 state plus deletion-protected DynamoDB locking
- ECS scaling: CPU target tracking for each service (1–2 tasks, 65% target)
- Disabled optional services: WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS

## Planned public routes

| Route | Destination |
| --- | --- |
| `/*` | Frontend service |
| `/api/*` | Backend service |
| `/frontend/healthz`, `/frontend/version` | Frontend service |
| `/backend/healthz`, `/backend/version` | Backend service |

## High-level solution architecture

```mermaid
flowchart LR
    users[Internet users] --> cloudflare[Cloudflare DNS<br/>asksafe.ai]
    cloudflare -->|NS delegation| route53[Route 53<br/>happy-post.asksafe.ai]
    route53 -->|A alias resolution| alb[Internet-facing ALB<br/>HTTPS :443]
    acm[ACM public certificate] -. "TLS certificate" .-> alb
    alb -->|/*| frontend[Frontend ECS Fargate<br/>Next.js]
    alb -->|/api/*| backend[Backend ECS Fargate<br/>FastAPI]
    backend -->|PostgreSQL 5432| rds[Private RDS PostgreSQL]
    frontend -. logs .-> logs[CloudWatch Logs]
    backend -. logs .-> logs
```

The diagram shows DNS delegation and high-level request routing. Cloudflare remains the parent DNS provider for `asksafe.ai` and delegates `happy-post.asksafe.ai` to the Route 53 hosted zone. Route 53 resolves the application domain to the internet-facing ALB; ACM terminates HTTPS at that ALB.

The maintainable logical source is [solution architecture](docs/diagrams/solution-architecture.mmd). The focused [runtime diagram](docs/diagrams/aws-ecs-runtime-architecture.drawio.svg) and [delivery/control-plane diagram](docs/diagrams/delivery-and-control-plane.drawio.svg) are explained in [Architecture](docs/architecture.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Networking](docs/networking.md)
- [CI/CD and control plane](docs/cicd.md)
- [Requirements traceability](docs/requirements-traceability.md)
- [Implementation backlog](docs/implementation-backlog.md)
- [Security decisions](docs/security-decisions.md)
- [Deployment and rollback](docs/deployment-and-rollback.md)
- [Operations](docs/operations.md)
- [Git and pull-request conventions](docs/git-and-pr-conventions.md)
- [Diagram sources](docs/diagrams/)

## Bootstrap status

CloudFormation bootstrap created the private state bucket `happy-post-tfstate-893794041695-ap-southeast-2` and lock table `happy-post-sandbox-terraform-lock`, using logical state prefix `sandbox/`. Its version-controlled source is [infra/bootstrap/happy-post-terraform-bootstrap.yaml](infra/bootstrap/happy-post-terraform-bootstrap.yaml). The state bucket is versioned and retained; the lock table is deletion-protected and retained on bootstrap stack delete or replacement. Sandbox has no required reviewers. A deliberate bootstrap teardown requires documented approval, safe removal of dependent Terraform state, disabling DynamoDB deletion protection, then explicit deletion of the retained lock table. Do not place credentials, tokens, or other secret values in this repository.
