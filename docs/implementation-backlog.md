# Implementation Backlog

The documentation baseline and application MVPs are complete. The remaining work is deliberately ordered so that local containers precede infrastructure and automation.

## P0 — Documentation baseline (complete)

- [x] Initialise local Git without commits, branches, remotes, or pull requests.
- [x] Record architecture, traceability, security, deployment, and Git/PR conventions.
- [x] Record the delegated Route 53 hosted-zone configuration.

## P1 — Backend MVP

- [x] Create the FastAPI backend application.
- [x] Implement `/healthz`, `/version`, `/backend/healthz`, and `/backend/version`, plus the assessment API contract under `/api/*`.
- [x] Define the PostgreSQL data model and migration approach required by the backend.
- [x] Add unit tests, linting, dependency management, and local configuration examples without secrets.

## P2 — Frontend MVP

- [x] Create the Next.js frontend application.
- [x] Integrate it with the backend’s `/api/*` contract.
- [x] Add frontend checks and `/healthz`, `/version`, `/frontend/healthz`, and `/frontend/version` endpoints.

## P3 — Local containers

- [ ] Add separate frontend and backend Dockerfiles.
- [ ] Add local development orchestration only if it supports the documented assessment workflow.
- [ ] Verify each image exposes only the needed runtime interface.

## P4 — AWS foundation

- [ ] Apply the reviewed CloudFormation bootstrap after supplying the required OIDC, GitHub-subject, and unique state-bucket inputs.
- [ ] Implement Terraform foundation and workload stacks using the documented ownership boundary.
- [ ] Implement the private RDS PostgreSQL data stack, database subnets/security group, and Secrets Manager credential integration.
- [ ] Configure the approved sandbox RDS settings: PostgreSQL 16.x availability check, db.t4g.micro, Single-AZ, encrypted gp3 storage (20–40 GiB), seven-day PITR, documented windows, and final-snapshot lifecycle.
- [ ] Configure frontend and backend CPU target-tracking scaling: minimum one task, maximum two tasks, 65% CPU target.
- [ ] Configure ACM and Route 53 records within the delegated hosted zone.

## P5 — CI/CD and operational validation

- [ ] Implement CI checks, image publication, workflow-dispatch-only Terraform apply/destroy controls, ECS deployment, smoke tests, and rollback automation.
- [ ] Configure the single GitHub environment, `sandbox`, without required reviewers and validate role separation.

## Deferred options

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are not assessment-baseline work. Each requires an explicit design decision before implementation.
