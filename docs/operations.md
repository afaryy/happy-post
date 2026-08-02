# Operations

## Scope

This document records the operational baseline for the single sandbox environment. The network foundation is applied; Aurora and workload resources remain pending a future approved workflow-dispatch apply.

## Service health and observability

- Both services must expose container-local `/healthz` and `/version`. The frontend must additionally expose `/frontend/healthz` and `/frontend/version`; the backend must additionally expose `/backend/healthz` and `/backend/version` for public ALB validation.
- The ALB publishes the component-specific public health routes defined in [Architecture](architecture.md).
- ECS task logs go to component-specific CloudWatch log groups.
- Deployment verifies ECS service stability and the relevant public health route before it succeeds.
- Notifications are intentionally outside the current baseline. Failed workflows and CloudWatch alarms remain visible in their respective consoles until a notification integration is separately approved.

## Database operations

- Aurora PostgreSQL Serverless remains private and is reachable only from the backend service.
- Database credentials are held only in the fixed Secrets Manager secret `happy-post-sandbox-database-credentials`; operators must not retrieve or place them in repository files.
- Aurora uses PostgreSQL 16.14 at initial creation with automatic minor-version upgrades enabled. Terraform verifies an available Aurora PostgreSQL 16.14 release in ap-southeast-2 before apply.
- Aurora uses one private `db.serverless` writer with encrypted Aurora standard storage. Its 0–1 ACU range is an assessment cost guardrail rather than workload sizing. The zero minimum permits Aurora auto-pause when supported by the selected engine; keep database connections closed outside active work. Increase the one-ACU maximum only through a reviewed Terraform change after observing CloudWatch CPU and connection metrics.
- Aurora automated backups and point-in-time recovery are configured for one day, the Aurora minimum selected for active Free Plan validation. Preferred backup window is 15:30-16:00 UTC daily; preferred maintenance window is sun:16:30-sun:17:00 UTC. This is an approved sandbox deviation from the former seven-day objective. The next approved apply must verify that the Free Plan accepts it; a future paid environment must restore a seven-day-or-greater recovery objective.
- Deletion protection is disabled for sandbox. Intentional destroy creates a uniquely named final cluster snapshot, does not retain automated backups, and requires the snapshot owner to review and delete it within seven days unless retention is explicitly approved.
- Restore testing is required before a release and after every database-changing migration. Restore to an isolated temporary private Aurora cluster and writer, verify availability, approved private connectivity, SELECT 1, migration version, and row-count sanity check, record evidence, then remove the temporary restore resources.
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
