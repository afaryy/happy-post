# Operations

## Scope

This document records the operational baseline for the single sandbox environment. The network and private RDS PostgreSQL data foundations are applied. The platform root is implemented but remains pending a future approved workflow-dispatch apply; workload resources remain pending.

## Service health and observability

- Both services must expose container-local `/healthz` and `/version`. The frontend must additionally expose `/frontend/healthz` and `/frontend/version`; the backend must additionally expose `/backend/healthz` and `/backend/version` for public ALB validation.
- The ALB publishes the component-specific public health routes defined in [Architecture](architecture.md).
- The platform root defines component-specific CloudWatch log groups with fourteen-day sandbox retention. ECS task logs use them after the later service deployment.
- Deployment verifies ECS service stability and the relevant public health route before it succeeds.
- Notifications are intentionally outside the current baseline. Failed workflows and CloudWatch alarms remain visible in their respective consoles until a notification integration is separately approved.

## Database operations

- RDS PostgreSQL remains private and is reachable only from the backend service.
- Database credentials are held only in the fixed Secrets Manager secret `happy-post-sandbox-database-credentials`; operators must not retrieve or place them in repository files.
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
