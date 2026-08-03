# Implementation Backlog

The documentation baseline and application MVPs are complete. The remaining work is deliberately ordered so that local containers precede infrastructure and automation.

## P0 — Documentation baseline (complete)

- [x] Initialise local Git without commits, branches, remotes, or pull requests.
- [x] Record architecture, traceability, security, deployment, and Git/PR conventions.
- [x] Record the delegated Route 53 hosted-zone configuration.

## P1 — Backend MVP

- [x] Create the FastAPI backend application.
- [x] Implement `/healthz`, `/version`, `/backend/healthz`, and `/backend/version`, plus the initial API contract under `/api/*`.
- [x] Define the PostgreSQL data model and migration approach required by the backend.
- [x] Add unit tests, linting, dependency management, and local configuration examples without secrets.

## P2 — Frontend MVP

- [x] Create the Next.js frontend application.
- [x] Integrate it with the backend’s `/api/*` contract.
- [x] Add frontend checks and `/healthz`, `/version`, `/frontend/healthz`, and `/frontend/version` endpoints.

## P3 — Local containers

- [x] Add separate frontend and backend Dockerfiles.
- [x] Add local development orchestration that supports the documented development workflow.
- [x] Verify each image exposes only the needed runtime interface.

## P4 — AWS foundation

- [x] Apply and post-bootstrap validate the CloudFormation bootstrap with the required OIDC, immutable GitHub subject, state bucket, DynamoDB locking, and retention controls.
- [x] Implement and locally validate the remote-state configuration and two-AZ network foundation, including subnet, route, NAT, and security-group boundaries.
- [x] Apply and reconcile the network root, including the backend-only PostgreSQL security-group boundary.
- [x] Implement, apply, and validate the private RDS PostgreSQL data stack, database subnet group, and Secrets Manager credential integration through the manual `data` target.
- [x] Record the approved Free Plan deviation: the active account rejects seven-day retention and Aurora Express Configuration cannot meet private VPC controls. The deployed RDS PostgreSQL 16.14 `db.t4g.micro` uses private VPC access, encrypted gp3 storage (20–40 GiB), Single-AZ, one-day PITR, documented windows, and final-snapshot lifecycle.
- [x] Implement, apply, and reconcile the independent platform root: two private ECR repositories, one ECS cluster, component log groups, and separate frontend/backend task and execution roles bounded by the bootstrap permissions boundary.
- [x] Apply and validate the public edge root: ACM certificate, HTTPS ALB, target groups, listener rules, and Route 53 records only inside the delegated hosted zone.
- [x] Define independent frontend and backend ECS service roots: required digest-pinned initial task definitions, private service networking, target-group attachment, backend-only RDS secret injection, and deployment-safe task-definition drift handling.
- [x] Define frontend and backend CPU target-tracking scaling: minimum one task, maximum two tasks, 65% CPU target.
- [x] Apply the network HTTP redirect ingress, rotate the database secret to include `database_url`, and apply the edge root.
- [x] Publish and scan frontend and backend images, then bootstrap each component service root with its real immutable digest.
- [ ] Perform the required isolated RDS restore test before the first database-changing release or migration.

## P5 — CI/CD and operational validation

- [x] Implement changed-root backend-free Terraform format, validate, native test, and TFLint checks on pull requests, plus workflow-dispatch-only plan/apply/destroy controls with a fixed canonical-root target allow-list.
- [x] Implement changed-component backend and frontend CI checks: locked dependencies, linting, unit tests, and frontend production build, without AWS credentials.
- [x] Implement Trivy, Snyk, and SonarQube Cloud security scanning with explicit scanner gates and fork-safe secret boundaries.
- [x] Remediate the Starlette HIGH findings and record the two approved, time-bound Trivy infrastructure exceptions for baseline sandbox trade-offs.
- [x] Implement main-only changed-component image publication with a Trivy image gate, immutable ECR publication, and digest-handoff artifacts.
- [x] Implement manual component-selected service bootstrap with immutable-digest validation and repository-specific ECR verification.
- [x] Implement post-bootstrap component-selected ECS deployment, health verification, and known-good rollback workflows.
- [x] Restrict the single GitHub environment, `sandbox`, to deployment branch `main` while retaining no required reviewers; then validate plan, apply, publish, and deployment role separation.
- [x] Execute controlled backend and frontend ECS deployments and public HTTPS smoke tests through the post-bootstrap deployment workflow.
- [ ] Rehearse component rollback only if time permits before assessment submission.

## P6 — Database-backed Three Happy Things MVP

- [x] Replace the temporary posts board with a warm bedtime MVP that starts with three small happy things and allows more.
- [x] Implement the `/api/entries/*` contract for today, month history, and date lookup.
- [x] Add MVP email/password sign-up and sign-in so each user sees only their own happy-things history.
- [x] Preserve append-only Alembic history by keeping `0001_create_posts` and adding `0002_create_users_daily_entries`, which replaces temporary posts with `users`, `user_sessions`, `daily_entries`, and `daily_entry_items`.
- [x] Update local Compose to run PostgreSQL and apply migrations before backend startup.
- [x] Add frontend loading, validation, success, error, and simple monthly history states.
- [x] Publish new immutable frontend and backend images from merged P6 `main`.
- [x] Merge the controlled database migration workflow, update the CloudFormation bootstrap stack, then run `alembic upgrade head` as a one-off private ECS task from the verified backend image digest.
- [x] Deploy the P6 backend, deploy the P6 frontend, then verify entry persistence through RDS.
- [ ] Re-run the restart persistence demo: create an entry, restart backend, and confirm the happy things remain.
- [ ] For real users, replace MVP app-level auth with managed identity such as Amazon Cognito, Auth0, or Clerk.

## Deferred options

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are not current-baseline work. Each requires an explicit design decision before implementation.
