# Deployment and Rollback

## Local P3 runbook

P3 provides local container validation only; it does not deploy to AWS, ECS, an
ALB, OIDC, or RDS. From the repository root, use:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

Compose runs `db`, `backend-migrate`, `backend`, and `frontend`, with loopback
bindings `127.0.0.1:5432`, `127.0.0.1:8000`, and `127.0.0.1:3000` by default.
If another local process owns port 8000 or 5432, use
`HAPPY_POST_BACKEND_HOST_PORT=18000` or `HAPPY_POST_DB_HOST_PORT=15432` before
each command; these change only host-side ports. The frontend remains at
`http://127.0.0.1:3000`, uses its container-local `/healthz`, and proxies
`/api/entries/*` internally to `http://backend:8000`. Stop the local stack with
the same overrides when they were used to start it.

## Deployment model

After a merge to `main`, the image-publication workflow determines which component changed, builds that component, blocks HIGH/CRITICAL Trivy findings, and publishes only the matching private ECR repository with an immutable `sha-<commit>` tag. It queries the pushed SHA-256 digest from ECR and retains a seven-day digest-handoff artifact containing the component, repository, digest, and source commit. The workflow uses the main-branch ECR-publish OIDC role only after the image passes the Trivy gate. Before initial service creation, manually dispatch the same workflow from `main` with `component=all` (or one named component) to publish the current source without requiring a new application-code change.

Initial service creation is separate and manual. An operator copies both `digest` and `source_commit` from the matching image-publication artifact into the `Bootstrap ECS Service` workflow, selects the same component, and enters `bootstrap-<component>`. The workflow resolves immutable `main`, rejects invalid and all-zero digests, requires a full lowercase source SHA already reachable from `main`, assumes the sandbox Terraform-apply role, verifies that the digest exists in the matching ECR repository and has the immutable `sha-<source_commit>` tag, then applies only that component's Terraform service root. Sandbox has no required reviewers or manual approval gate, but its GitHub Environment deployment-branch rule must restrict privileged workflow dispatches to `main`. It is an OIDC/configuration boundary.

An ECR image push does not update ECS by itself. The bootstrap workflow uses a verified digest to create the initial task definition and selected ECS service. The separate `Deploy ECS Service` workflow registers subsequent digest-pinned task-definition revisions, updates only the selected existing service, waits for stability, validates ALB target health, and runs the component public HTTPS smoke test.

Terraform provisions the stable edge and service infrastructure and an initial task definition. The edge root created ACM DNS validation, the public ALB, HTTP-to-HTTPS redirect, HTTPS routing, and the Route 53 alias inside the delegated zone. The independent frontend-service and backend-service roots require real scanned image digests, so they must not be applied with example placeholder values. Terraform ignores the service `task_definition` field after initial creation so that a later valid delivery workflow cannot be undone by Terraform drift reconciliation.

Terraform infrastructure apply is separate from application delivery. It is started only by workflow dispatch; the workflow resolves and logs the current immutable `main` commit, creates a fresh plan for that checkout, and applies that exact plan through the `sandbox` OIDC role. A merge never applies Terraform. Destroy is separately dispatched with explicit confirmation and the same immutable-main resolution.

The Terraform test workflow runs backend-free validation for every Terraform-related pull request. The manual plan workflow and manual apply/destroy workflows select a canonical root through the same fixed `target` allow-list; they resolve and log the immutable `origin/main` SHA when dispatched. Plan assumes the read-only plan role and uploads a rendered artifact. Apply creates a fresh plan in the same job and applies that exact file through the separate apply role. Apply and destroy confirmations are `apply-<target>` and `destroy-<target>`. A target missing from the resolved commit fails before credentials are configured. The applied `network`, `data`, `platform`, `edge`, `backend-service`, and `frontend-service` roots are current implemented targets. Publish and scan a changed component image, then use `Deploy ECS Service` rather than the initial-only bootstrap workflow. The deployment workflow checks digest/source-commit provenance, tags the healthy predecessor known-good, updates only the selected service, and verifies stability, target health, and public HTTPS health.

The bootstrap state bucket and DynamoDB lock table are not workload-destroy targets. The bucket is retained and the lock table is deletion-protected and retained. A deliberate bootstrap teardown requires documented approval, safe removal of all dependent Terraform state, disabling lock-table deletion protection, then explicit lock-table deletion.

Both frontend and backend have now been deployed through the controlled ECS deployment workflow. Backend smoke tests passed at `/backend/healthz` and `/backend/version`; frontend smoke tests passed at `/healthz` and `/version`. The backend version endpoint reports the deployed immutable image digest. The frontend version endpoint currently reports the application version `0.1.0`.

The private RDS PostgreSQL data stack is provisioned separately from application services. The Three Happy Things MVP keeps append-only migration history: `0001_create_posts` remains as the original temporary schema and `0002_create_users_daily_entries` replaces `posts` with `users`, `user_sessions`, `daily_entries`, and `daily_entry_items`. Each signed-in user owns their own daily history, and one day can hold three or more happy items. Database migrations must be backward-compatible, run before the backend version that requires them, and have a documented restore or compensating-migration approach before deployment. The active Free Plan rejected the former seven-day retention objective and permits the deployed private RDS configuration with one-day PITR. It must not upgrade the account plan automatically. A future paid environment must restore a seven-day-or-greater recovery objective.

## Database migration workflow

Database migrations are manual and run only from `main` through the `sandbox` environment. The `Run Database Migration` workflow accepts the backend image `image_digest`, the matching full lowercase `source_commit`, and the confirmation value `migrate-backend`. It rejects invalid or all-zero digests, verifies that the digest exists in `happy-post-sandbox-backend`, and confirms that the image has the immutable `sha-<source_commit>` tag before any ECS task is started.

The workflow registers a one-off `happy-post-sandbox-backend-migration` task definition from the currently deployed backend task-definition shape, replaces only the backend image with the verified digest, sets the command to `alembic upgrade head`, and runs it once on Fargate using the existing backend service private subnet and security-group configuration. `DATABASE_URL` is still injected by the backend execution role from Secrets Manager at task launch; the workflow must never print the connection string or secret values. It waits for the task to stop and fails unless the backend container exits with code `0`.

For a database-changing backend release, use this sequence:

1. Publish the backend image from `main` and capture the digest-handoff artifact.
2. Run `Run Database Migration` with the backend `image_digest`, `source_commit`, and `migrate-backend`.
3. Confirm the migration task succeeded.
4. Run `Deploy ECS Service` for `backend` with the same digest and source commit.
5. Deploy the frontend only after the backend is healthy when the frontend depends on the changed API.

After the migration workflow is merged, update the `happy-post-sandbox-bootstrap` CloudFormation stack before using it. The workflow depends on the bootstrap-managed ECS deploy role having scoped `ecs:RunTask` permission for the backend migration task-definition family.

## Verification

The deployment workflow must wait for ECS service stability and verify the component-specific public routes:

| Component | Verification routes |
| --- | --- |
| Frontend | `/healthz`, `/version` |
| Backend | `/backend/healthz`, `/backend/version` |

Container-local health checks are still evaluated inside ECS. The deployment workflow smoke tests use the public ALB routes listed above.

## Rollback

If a deployment fails health checks, ECS stability checks, or smoke tests, `Deploy ECS Service` restores the captured predecessor task definition, waits for stability, and reruns the component smoke test before reporting failure. For an intentional rollback, `Roll Back ECS Service` selects only the affected component and its immediately preceding task-definition revision tagged `HappyPostDeploymentStatus=known-good`; it waits for stability and reruns the same smoke test. Rollback uses the prior immutable image digest; it never relies on a mutable `latest` tag. A rollback does not roll back database schema. The rollback workflow is available and should be rehearsed only if time permits before assessment submission.

If the migration succeeds but the backend deployment fails, first allow the deployment workflow to restore the prior backend task definition. Then decide whether the successful migration is backward-compatible with the old backend. If it is compatible, keep the schema and retry the fixed backend deployment. If it is not compatible, use the documented restore or compensating-migration plan; do not run an automatic schema rollback from the ECS rollback workflow.

## Scope limits

Blue/green deployment and notification integrations are optional enhancements and disabled in the current baseline. Baseline rollback is an ECS rolling deployment rollback for one affected service at a time.
