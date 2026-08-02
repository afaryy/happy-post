# Implementation Backlog

The documentation baseline and application MVPs are complete. The remaining work is deliberately ordered so that local containers precede infrastructure and automation.

## P0 — Documentation baseline (complete)

- [x] Initialise local Git without commits, branches, remotes, or pull requests.
- [x] Record architecture, traceability, security, deployment, and Git/PR conventions.
- [x] Record the delegated Route 53 hosted-zone configuration.

## P1 — Backend MVP

- [x] Create the FastAPI backend application.
- [x] Implement `/healthz`, `/version`, `/backend/healthz`, and `/backend/version`, plus the posts API contract under `/api/*`.
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
- [ ] Publish and scan frontend and backend images, then bootstrap each component service root with its real immutable digest.
- [ ] Perform the required isolated RDS restore test before the first database-changing release or migration.

## P5 — CI/CD and operational validation

- [x] Implement changed-root backend-free Terraform format/validate/TFLint on pull requests, plus workflow-dispatch-only plan/apply/destroy controls with a fixed canonical-root target allow-list.
- [x] Implement changed-component backend and frontend CI checks: locked dependencies, linting, unit tests, and frontend production build, without AWS credentials.
- [x] Implement Trivy, Snyk, and SonarQube Cloud security scanning with explicit scanner gates and fork-safe secret boundaries.
- [x] Remediate the Starlette HIGH findings and record the two approved, time-bound Trivy infrastructure exceptions for baseline sandbox trade-offs.
- [x] Implement main-only changed-component image publication with a Trivy image gate, immutable ECR publication, and digest-handoff artifacts.
- [x] Implement manual component-selected service bootstrap with immutable-digest validation and repository-specific ECR verification.
- [ ] Implement post-bootstrap ECS deployment, smoke tests, and rollback automation.
- [ ] Configure the single GitHub environment, `sandbox`, without required reviewers and validate role separation.

## Deferred options

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are not current-baseline work. Each requires an explicit design decision before implementation.
