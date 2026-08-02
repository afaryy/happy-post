# Deployment and Rollback

## Local P3 runbook

P3 provides local container validation only; it does not deploy to AWS, ECS, an
ALB, OIDC, or RDS. From the repository root, use:

```bash
docker compose up --build -d
docker compose ps
docker compose down --remove-orphans
```

Compose runs only `backend` and `frontend`, with loopback bindings
`127.0.0.1:8000` and `127.0.0.1:3000` by default. If another local process owns
port 8000, use `HAPPY_POST_BACKEND_HOST_PORT=18000` before each command; this
changes only the backend's host-side port. The frontend remains at
`http://127.0.0.1:3000`, uses its container-local `/healthz`, and proxies
`/api/posts` internally to `http://backend:8000`. Stop the local stack with the
same override when one was used to start it.

## Deployment model

After a merge to `main`, the image-publication workflow determines which component changed, builds that component, blocks HIGH/CRITICAL Trivy findings, and publishes only the matching private ECR repository with an immutable `sha-<commit>` tag. It queries the pushed SHA-256 digest from ECR and retains a seven-day digest-handoff artifact containing the component, repository, digest, and source commit. The workflow uses the main-branch ECR-publish OIDC role only after the image passes the Trivy gate. Before initial service creation, manually dispatch the same workflow from `main` with `component=all` (or one named component) to publish the current source without requiring a new application-code change.

Initial service creation is separate and manual. An operator copies both `digest` and `source_commit` from the matching image-publication artifact into the `Bootstrap ECS Service` workflow, selects the same component, and enters `bootstrap-<component>`. The workflow resolves immutable `main`, rejects invalid and all-zero digests, requires a full lowercase source SHA already reachable from `main`, assumes the sandbox Terraform-apply role, verifies that the digest exists in the matching ECR repository and has the immutable `sha-<source_commit>` tag, then applies only that component's Terraform service root. Sandbox has no required reviewers or manual approval gate. It is an OIDC/configuration boundary.

An ECR image push does not update ECS by itself. The bootstrap workflow uses a verified digest to create the initial task definition and selected ECS service. A later, separate deployment workflow will register subsequent digest-pinned task-definition revisions, update only the selected existing service, wait for stability, and run component smoke tests.

Terraform provisions the stable edge and service infrastructure and an initial task definition. The edge root created ACM DNS validation, the public ALB, HTTP-to-HTTPS redirect, HTTPS routing, and the Route 53 alias inside the delegated zone. The independent frontend-service and backend-service roots require real scanned image digests, so they must not be applied with example placeholder values. Terraform ignores the service `task_definition` field after initial creation so that a later valid delivery workflow cannot be undone by Terraform drift reconciliation.

Terraform infrastructure apply is separate from application delivery. It is started only by workflow dispatch; the workflow resolves and logs the current immutable `main` commit, creates a fresh plan for that checkout, and applies that exact plan through the `sandbox` OIDC role. A merge never applies Terraform. Destroy is separately dispatched with explicit confirmation and the same immutable-main resolution.

The Terraform test workflow runs backend-free validation for every Terraform-related pull request. The manual plan workflow and manual apply/destroy workflows select a canonical root through the same fixed `target` allow-list; they resolve and log the immutable `origin/main` SHA when dispatched. Plan assumes the read-only plan role and uploads a rendered artifact. Apply creates a fresh plan in the same job and applies that exact file through the separate apply role. Apply and destroy confirmations are `apply-<target>` and `destroy-<target>`. A target missing from the resolved commit fails before credentials are configured. The applied `network`, `data`, `platform`, and `edge` roots are current implemented targets. Publish and scan the required component image, then use the controlled service-bootstrap workflow to apply its matching service root with the verified real digest. Bootstrap the backend before the frontend when bringing up the full application, because the frontend's `/api/*` route depends on the backend target group being healthy.

The bootstrap state bucket and DynamoDB lock table are not workload-destroy targets. The bucket is retained and the lock table is deletion-protected and retained. A deliberate bootstrap teardown requires documented approval, safe removal of all dependent Terraform state, disabling lock-table deletion protection, then explicit lock-table deletion.

The private RDS PostgreSQL data stack is provisioned separately from application services. Database migrations must be backward-compatible, run before the backend version that requires them, and have a documented restore or compensating-migration approach before deployment. The active Free Plan rejected the former seven-day retention objective and permits the deployed private RDS configuration with one-day PITR. It must not upgrade the account plan automatically. A future paid environment must restore a seven-day-or-greater recovery objective.

## Verification

The deployment workflow must wait for ECS service stability and verify the component-specific public routes:

| Component | Verification routes |
| --- | --- |
| Frontend | `/frontend/healthz`, `/frontend/version` |
| Backend | `/backend/healthz`, `/backend/version` |

The internal container `/healthz` route remains private and is not used as an external ALB smoke-test path.

## Rollback

If a deployment fails health checks, ECS stability checks, or smoke tests, the deployment must stop and roll back the affected service to its immediately preceding known-good task-definition revision. The workflow must then wait for stability and rerun the relevant smoke tests. Rollback uses the prior immutable image digest; it must never rely on a mutable `latest` tag.

## Scope limits

Blue/green deployment and notification integrations are optional enhancements and disabled in the current baseline. Baseline rollback is an ECS rolling deployment rollback for one affected service at a time.
