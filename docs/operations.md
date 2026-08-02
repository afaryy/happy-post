# Operations

## Scope

This document records the operational baseline for the single sandbox environment. No AWS resources or operational automation exist yet; the requirements below govern the later implementation.

## Service health and observability

- Both services must expose container-local `/healthz` and `/version`. The frontend must additionally expose `/frontend/healthz` and `/frontend/version`; the backend must additionally expose `/backend/healthz` and `/backend/version` for public ALB validation.
- The ALB publishes the component-specific public health routes defined in [Architecture](architecture.md).
- ECS task logs go to component-specific CloudWatch log groups.
- Deployment verifies ECS service stability and the relevant public health route before it succeeds.
- Notifications are intentionally outside the assessment baseline. Failed workflows and CloudWatch alarms remain visible in their respective consoles until a notification integration is separately approved.

## Database operations

- RDS PostgreSQL remains private and is reachable only from the backend service.
- Database credentials are held in Secrets Manager; operators must not retrieve or place them in repository files.
- RDS uses PostgreSQL 16.14 at initial creation with automatic minor-version upgrades enabled. Terraform verifies an available PostgreSQL 16.x release in ap-southeast-2 before apply.
- RDS is a Single-AZ db.t4g.micro instance with encrypted gp3 storage: 20 GiB allocated and 40 GiB maximum autoscaled storage. It uses the AWS-managed RDS KMS key; customer-managed KMS is deferred.
- RDS automated backups and point-in-time recovery retain seven days. Preferred backup window is 15:30-16:00 UTC daily; preferred maintenance window is sun:16:30-sun:17:00 UTC.
- Deletion protection is disabled for sandbox. Intentional destroy creates a uniquely named final snapshot, does not retain automated backups, and requires the snapshot owner to review and delete it within seven days unless retention is explicitly approved.
- Restore testing is required before assessment submission and after every database-changing migration. Restore to an isolated temporary private instance, verify availability, approved private connectivity, SELECT 1, migration version, and row-count sanity check, record evidence, then remove the temporary instance.
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
