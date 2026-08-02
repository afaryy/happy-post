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
- [ ] Implement the remaining Terraform foundation and workload stacks using the documented ownership boundary.
- [x] Implement and validate the private Aurora PostgreSQL Serverless data stack, database subnet group, and Secrets Manager credential integration; do not apply it locally.
- [x] Replace the standard RDS design because the active Free Plan rejected seven-day retention. The first Aurora attempt confirmed the same restriction; retain PostgreSQL 16.14, private VPC access, encrypted Aurora storage, a 0–1 ACU assessment cost guardrail, one-day PITR as the approved sandbox candidate, documented windows, and final-cluster-snapshot lifecycle.
- [ ] Apply the data root through the manual `data` target only after the reviewed plan is approved, and verify one-day Aurora retention after creation.
- [ ] Configure frontend and backend CPU target-tracking scaling: minimum one task, maximum two tasks, 65% CPU target.
- [ ] Configure ACM and Route 53 records within the delegated hosted zone.

## P5 — CI/CD and operational validation

- [x] Implement changed-root backend-free Terraform format/validate/TFLint on pull requests, plus workflow-dispatch-only plan/apply/destroy controls with a fixed canonical-root target allow-list.
- [x] Implement changed-component backend and frontend CI checks: locked dependencies, linting, unit tests, and frontend production build, without AWS credentials.
- [x] Implement Trivy, Snyk, and SonarQube Cloud security scanning with explicit scanner gates and fork-safe secret boundaries.
- [x] Remediate the Starlette HIGH findings and record the two approved, time-bound Trivy infrastructure exceptions for baseline sandbox trade-offs.
- [ ] Implement image publication, ECS deployment, smoke tests, and rollback automation.
- [ ] Configure the single GitHub environment, `sandbox`, without required reviewers and validate role separation.

## Deferred options

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are not current-baseline work. Each requires an explicit design decision before implementation.
