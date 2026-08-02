# Security Decisions

## Identity and GitHub controls

GitHub Actions authenticates to AWS with GitHub OIDC and temporary STS credentials; no long-lived AWS access keys are stored in repository secrets. The only GitHub environment is `sandbox`; it supplies an OIDC/configuration boundary but has no required reviewers or manual approval gate. It is used by manual Terraform plan, apply, destroy, ECS deployment, and rollback workflows. Pull requests receive no AWS credentials and run backend-free validation only.

Application CI runs backend and frontend lint, unit-test, and build checks without AWS credentials, secrets, or GitHub environment access. It is therefore safe for same-repository and fork pull requests.

Security CI has no AWS credentials or GitHub environment access. Trivy scans secrets for every pull request and `main` push; any detected secret blocks the workflow pending verification. Its dependency and IaC scan blocks HIGH/CRITICAL findings. Snyk and SonarQube Cloud run only for same-repository pull requests and `main` pushes because GitHub does not provide repository secrets to fork pull requests. Snyk receives only `SNYK_TOKEN` and blocks HIGH/CRITICAL dependency or IaC findings. SonarQube Cloud receives only `SONAR_TOKEN` plus the non-sensitive `SONAR_ORGANIZATION` and `SONAR_PROJECT_KEY` variables; it scans the combined Happy Post project and waits for its quality gate. Container-image scanning is deferred until the image-publication workflow builds the frontend and backend images.

One GitHub environment does not mean one AWS role. Separate IAM roles preserve operational boundaries for Terraform planning, Terraform apply/destroy, image publishing, and ECS deployment. The plan role is restricted to the approved repository's `pull_request` claim; Terraform apply/destroy and ECS deployment roles are restricted to its `environment:sandbox` claim; the ECR publish role is restricted to its `ref:refs/heads/main` claim.

The Terraform test workflow maps changed files to a fixed allow-list of canonical roots and runs backend-free validation only; a shared module or Terraform workflow change validates every implemented root. The manual plan workflow uses `happy-post-sandbox-terraform-plan` only from `environment:sandbox`, resolves and logs immutable `origin/main`, and accepts a fixed canonical-root `target` mapped to a fixed directory. Apply and destroy use the separate `happy-post-sandbox-terraform-apply` role from the same environment; apply creates and applies an exact fresh plan in one job. A target missing from the resolved commit fails before credentials are configured. The workflow source contains role ARNs, which are non-secret account configuration; it contains no AWS access keys or secret values.

## Terraform state-backend protection

CloudFormation owns the private versioned S3 state bucket and the DynamoDB lock table. The lock table is encrypted, deletion-protected, and retained on bootstrap stack deletion or replacement. This prevents an accidental bootstrap teardown from silently removing Terraform's concurrency lock. A deliberate teardown requires documented approval, safe removal of dependent state, disabling DynamoDB deletion protection, and an explicit delete of the retained table.

## Runtime boundaries

The platform root defines separate frontend and backend task roles, execution roles, private image repositories, and component log groups. Both task roles have no identity-policy AWS API permissions. The frontend execution role can pull only its image and publish frontend logs; the backend execution role can pull only its image, publish backend logs, and—only in the backend-service root—read the named database secret during ECS task launch. Tasks remain private; only the ALB is internet-facing. The ALB security group permits TCP 80 only to redirect to HTTPS and HTTPS 443 for application traffic; task security groups accept application traffic only from the ALB security group. RDS PostgreSQL is private, has no public route or public IP, and accepts TCP 5432 only from the backend security group.

### Local P3 container boundary

The local Compose stack has exactly two services, `backend` and `frontend`; it
does not run PostgreSQL. Backend and frontend images use non-root runtime users.
Their published ports are loopback-only: backend defaults to `127.0.0.1:8000` and
frontend to `127.0.0.1:3000`. `HAPPY_POST_BACKEND_HOST_PORT` is a non-sensitive
temporary host-port override (for example, `18000`); it does not change the
container port or the internal frontend-to-backend route `http://backend:8000`.
Dockerfiles, Compose, and their build contexts contain no credentials or secret
values. This local-container work does not implement or alter ECS, ALB, OIDC, or
RDS controls.

## Secrets and configuration

No secret values belong in source control, documentation, GitHub variables, or container images. Terraform generates the database password and writes it to the fixed Secrets Manager secret `happy-post-sandbox-database-credentials`; it is sensitive in Terraform state and is never an output. The secret stores a URL-encoded `database_url` JSON key along with the discrete connection fields; the backend task definition injects only that key as `DATABASE_URL`. The bootstrap apply role receives scoped `secretsmanager:PutSecretValue` and `secretsmanager:GetSecretValue` for that secret: Terraform must read the version it writes to wait for provider confirmation. The read-only manual plan role receives `secretsmanager:GetSecretValue` only for the same secret and has no write permission. The backend task execution role is the only runtime workload role with `secretsmanager:GetSecretValue` for the named database secret. The frontend task role has no AWS API permissions. The hosted-zone ID, `Z07821441TT04VLUXZXPO`, is non-sensitive configuration and may be stored as a Terraform input or CI variable.

## Image and security governance

Images are versioned by immutable digest, stored in private ECR repositories, and scanned before deployment. Baseline deployment image selection must use approved, maintained base images and satisfy the scanner gates below. Fargate is serverless container compute, so Happy Post manages no EC2 AMIs; AWS manages the underlying host and platform images. CloudWatch log access is scoped to the specific Happy Post log groups. Cloudflare controls parent DNS for `asksafe.ai`; Route 53 controls only the delegated `happy-post.asksafe.ai` zone.

### Scanner gates and exceptions

- Snyk and Trivy block HIGH and CRITICAL findings.
- Any detected secret finding blocks the workflow pending verification.
- The SonarQube quality gate is required.
- A documented exception requires an owner, rationale, expiry date, and approver. It is time-bound and must be removed or renewed before expiry.

Current approved Trivy exceptions are limited to the following baseline trade-offs and are held in [`.trivyignore.yaml`](../.trivyignore.yaml), which the HIGH/CRITICAL Trivy vulnerability-and-IaC gate loads:

| Finding | Path | Owner / approver | Expiry | Rationale |
| --- | --- | --- | --- | --- |
| `AWS-0079` | `infra/terraform/stacks/data/main.tf` | afaryy / afaryy | 2026-11-02 | The sandbox RDS PostgreSQL instance uses AWS-managed encryption with `storage_encrypted` enabled. A customer-managed KMS key is deferred to avoid expanding the sandbox IAM and key-management surface. |
| `AWS-0132` | `infra/bootstrap/happy-post-terraform-bootstrap.yaml` | afaryy / afaryy | 2026-11-02 | The retained sandbox Terraform-state bucket uses SSE-S3; a customer-managed KMS key is deferred. |
| `AWS-0104` | `infra/terraform/foundations/network/main.tf` | afaryy / afaryy | 2026-11-02 | Private frontend and backend tasks require HTTPS egress through the single sandbox NAT Gateway for ECR, CloudWatch, and external dependencies while VPC endpoints are deferred. |
| `AWS-0053` | `infra/terraform/foundations/edge/main.tf` | afaryy / afaryy | 2026-11-02 | The internet-facing ALB is the approved HTTPS entry point for `happy-post.asksafe.ai`; only the ALB is public, while Fargate services and RDS remain private. |

These exceptions do not suppress dependency or secret findings. They must be removed, renewed with a new approval, or replaced by an implemented security control before expiry.

The only approved Snyk Open Source exception is held in
[`frontend/.snyk`](../frontend/.snyk), which the frontend dependency scan loads
explicitly:

| Finding | Scope | Owner / approver | Expiry | Rationale |
| --- | --- | --- | --- | --- |
| `SNYK-JS-NANOID-18506894`, `SNYK-JS-NANOID-18506897` | Frontend `package-lock.json` dependency path | afaryy / afaryy | 2026-08-16 | The current Next.js 16.2.12 → PostCSS CommonJS dependency path reaches Nanoid 3.3.16. The reported fixed Nanoid 5 line is ESM-only and would break PostCSS's `require('nanoid/non-secure')`; no compatible direct upgrade is available. |

This exception is limited to the named Snyk issue and expires automatically. It
does not suppress any other frontend dependency, backend dependency, IaC, Trivy,
secret, or SonarQube finding.

The permissions boundary, separate OIDC roles, narrowly scoped security groups, immutable images, scan gates, and time-bound exceptions are the baseline security-governance controls. They are reviewed through pull requests and must not be weakened without an explicit documented decision.

The Terraform apply role uses an explicit baseline action list rather than service-wide wildcard grants. Its Route 53 record changes are restricted to the delegated hosted-zone ARN. Terraform must tag every supported resource with `Project=happy-post` and `Environment=sandbox` so later IAM refinements can restrict mutation by resource tags and ARN.

## Optional services

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are disabled by default. They must not be represented as baseline security controls until separately approved and implemented.
