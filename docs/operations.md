# Operations

## Scope

This document records the operational baseline for the single sandbox environment. The network, private RDS PostgreSQL data, ECR/ECS platform, edge foundations, and both initial digest-pinned ECS services are applied. Frontend and backend services have been successfully deployed through the controlled ECS deployment workflow, and their public HTTPS smoke tests pass.

## Service health and observability

- Both services must expose container-local `/healthz` and `/version`. The frontend must additionally expose `/frontend/healthz` and `/frontend/version`; the backend must additionally expose `/backend/healthz` and `/backend/version` for public ALB validation.
- The ALB publishes the component-specific public health routes defined in [Architecture](architecture.md).
- The applied platform root defines component-specific CloudWatch log groups with fourteen-day sandbox retention. Both ECS services write only to their matching group.
- Each ECS service uses CPU target tracking: one to two tasks, 65% target CPU, 60-second scale-out cooldown, and 300-second scale-in cooldown.
- Deployment verifies ECS service stability and the relevant public health route before it succeeds.
- The `Publish Immutable Images` workflow creates a seven-day digest-handoff artifact for each changed component after a successful Trivy gate and ECR push. Before initial service creation, manually dispatch it from `main` with the required component or `all`. Use the matching artifact's `digest` and `source_commit` with `Bootstrap ECS Service`, select the same component, and enter `bootstrap-<component>`. The workflow validates the digest and full lowercase source SHA, rejects the all-zero example value, confirms that the digest belongs to the matching ECR repository with its `sha-<source_commit>` tag, then applies only that service root from immutable `main`.
- `Bootstrap ECS Service` is initial-creation-only. For a later component release, use `Deploy ECS Service` with the matching image-publication `digest`, `source_commit`, and `deploy-<component>` confirmation. It verifies ECR provenance, records the currently healthy task definition as known-good, registers a new digest-pinned revision, updates only that service, waits for ECS stability and a healthy ALB target, then calls the component public HTTPS health URL. It automatically restores the captured predecessor if its post-update verification fails.
- For an intentional component rollback, use `Roll Back ECS Service` with `rollback-<component>`. It selects only the immediately preceding task-definition revision that is tagged `HappyPostDeploymentStatus=known-good`; it fails safely if there is no such predecessor.
- Notifications are intentionally outside the current baseline. Failed workflows and CloudWatch alarms remain visible in their respective consoles until a notification integration is separately approved.

## Current deployed verification

The latest controlled ECS deployment verification passed:

| Component | Smoke-test routes | Version response |
| --- | --- | --- |
| Backend | `/backend/healthz`, `/backend/version` | Deployed immutable image digest |
| Frontend | `/healthz`, `/version` | Application version `0.1.0` |

The rollback workflow is available for component-scoped recovery. Rehearse rollback only if time permits before assessment submission; otherwise keep it as a documented follow-up because the deployment and public smoke path is already validated.

## Database operations

- RDS PostgreSQL remains private and is reachable only from the backend service.
- Database credentials are held only in the fixed Secrets Manager secret `happy-post-sandbox-database-credentials`; its `database_url` JSON key is injected at backend task launch. Operators must not retrieve or place it in repository files.
- ECS retrieves Secrets Manager values only when a task starts; it does not refresh values inside an already-running task. After rotating the database secret, deploy a new backend task-definition revision or force a backend service deployment, wait for healthy targets, then retire the prior tasks.
- RDS uses PostgreSQL 16.14 at creation with automatic minor-version upgrades enabled.
- RDS uses one private `db.t4g.micro` instance in Single-AZ with encrypted gp3 storage (20 GiB allocated, 40 GiB maximum). It is intentionally cost-conscious sandbox sizing; changes require a reviewed Terraform change after observing CloudWatch CPU, storage, and connection metrics.
- RDS automated backups and point-in-time recovery are configured for one day, the maximum permitted by the active Free Plan. Preferred backup window is 15:30-16:00 UTC daily; preferred maintenance window is sun:16:30-sun:17:00 UTC. This is an approved sandbox deviation from the former seven-day objective. A future paid environment must restore a seven-day-or-greater recovery objective.
- Deletion protection is disabled for sandbox. Intentional destroy creates a uniquely named final DB snapshot, does not retain automated backups, and requires the snapshot owner to review and delete it within seven days unless retention is explicitly approved.
- Restore testing is required before a release and after every database-changing migration. Restore to an isolated temporary private RDS instance, verify availability, approved private connectivity, `SELECT 1`, migration version, and a row-count sanity check, record evidence, then remove the temporary restore resources. This test remains outstanding because the application has not yet integrated with RDS.
- A database change requires a backward-compatible migration plan and either a restore plan or a compensating migration before deployment.

## Terraform state-backend operations

- The private versioned S3 state bucket and DynamoDB lock table are bootstrap-owned shared controls, not Terraform workload resources.
- The lock table is encrypted, deletion-protected, and retained when the bootstrap stack is deleted or replaced.
- Never disable deletion protection to resolve a Terraform lock. Investigate the lock owner and use Terraform's documented lock-recovery procedure only after confirming no plan or apply is running.
- A deliberate bootstrap teardown requires documented approval, safe removal of dependent state, disabling deletion protection, and an explicit delete of the retained lock table.

## Incident and rollback procedure

1. Identify whether the incident affects frontend, backend, shared infrastructure, or the database.
2. For a failed application deployment, roll back only the affected ECS service to the immediately preceding known-good task-definition revision and immutable image digest.
3. Wait for service stability and rerun that component's smoke checks.
4. Do not roll back database schema automatically. Use the approved restore or compensating-migration plan.
5. Record the cause, affected version, rollback revision, and follow-up action.

## Deferred operational capabilities

The following are not baseline services: WAF, Service Connect, blue/green deployments, VPC endpoints, end-to-end TLS, and notification integrations. They need a separate decision and implementation plan before use.
