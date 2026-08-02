# Security Decisions

## Identity and GitHub controls

GitHub Actions authenticates to AWS with GitHub OIDC and temporary STS credentials; no long-lived AWS access keys are stored in repository secrets. The only GitHub environment is `sandbox`; it supplies an OIDC/configuration boundary but has no required reviewers or manual approval gate. It is used by Terraform apply/destroy, ECS deployment, and rollback workflows. Same-repository pull-request Terraform plans use a separate `pull_request` OIDC subject and do not use the environment. Fork pull requests receive no AWS credentials and run backend-free validation only.

One GitHub environment does not mean one AWS role. Separate IAM roles preserve operational boundaries for Terraform planning, Terraform apply/destroy, image publishing, and ECS deployment. The plan role is restricted to the approved repository's `pull_request` claim; Terraform apply/destroy and ECS deployment roles are restricted to its `environment:sandbox` claim; the ECR publish role is restricted to its `ref:refs/heads/main` claim.

The initial Terraform controls use `happy-post-sandbox-terraform-plan` only in same-repository pull-request jobs. The plan job is fail-closed until the non-sensitive repository variable `ENABLE_TERRAFORM_PR_PLAN` is explicitly set to `true`. Backend-free validation is the only Terraform work available to forks. The test workflow maps changed files to a fixed allow-list of canonical roots and validates only affected implemented roots; a shared module or Terraform workflow change validates every implemented root. Apply and destroy use `happy-post-sandbox-terraform-apply` only from `environment:sandbox`, resolve and log the immutable `origin/main` SHA at dispatch, and create a fresh plan in the same job that applies it. Their `target` input is an allow-list of canonical Terraform roots, mapped to fixed directories rather than accepting a user-supplied path. A target missing from the resolved commit fails before credentials are configured. The workflow source contains role ARNs, which are non-secret account configuration; it contains no AWS access keys or secret values.

## Terraform state-backend protection

CloudFormation owns the private versioned S3 state bucket and the DynamoDB lock table. The lock table is encrypted, deletion-protected, and retained on bootstrap stack deletion or replacement. This prevents an accidental bootstrap teardown from silently removing Terraform's concurrency lock. A deliberate teardown requires documented approval, safe removal of dependent state, disabling DynamoDB deletion protection, and an explicit delete of the retained table.

## Runtime boundaries

Frontend and backend tasks use separate task roles, execution roles, security groups, image repositories, log groups, task-definition families, and ECS services. The frontend execution role pulls only its image and publishes frontend logs. The backend execution role pulls only its image, publishes backend logs, and is the only execution role allowed to retrieve the named database secret. Tasks remain private; only the ALB is internet-facing. The ALB security-group ingress is HTTPS only, and task security groups accept application traffic only from the ALB security group. RDS PostgreSQL is private, has no public route or public IP, and accepts TCP 5432 only from the backend security group.

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

No secret values belong in source control, documentation, GitHub variables, or container images. Database credentials are stored in AWS Secrets Manager and injected through the ECS backend task definition. Only the backend task execution role receives `secretsmanager:GetSecretValue` for the named database secret. The frontend task role has no AWS API permissions. The hosted-zone ID, `Z07821441TT04VLUXZXPO`, is non-sensitive configuration and may be stored as a Terraform input or CI variable.

## Image and security governance

Images are versioned by immutable digest, stored in private ECR repositories, and scanned before deployment. Baseline deployment image selection must use approved, maintained base images and satisfy the scanner gates below. Fargate is serverless container compute, so Happy Post manages no EC2 AMIs; AWS manages the underlying host and platform images. CloudWatch log access is scoped to the specific Happy Post log groups. Cloudflare controls parent DNS for `asksafe.ai`; Route 53 controls only the delegated `happy-post.asksafe.ai` zone.

### Scanner gates and exceptions

- Snyk and Trivy block HIGH and CRITICAL findings.
- Any verified secret finding blocks the workflow.
- The SonarQube quality gate is required.
- A documented exception requires an owner, rationale, expiry date, and approver. It is time-bound and must be removed or renewed before expiry.

The permissions boundary, separate OIDC roles, narrowly scoped security groups, immutable images, scan gates, and time-bound exceptions are the baseline security-governance controls. They are reviewed through pull requests and must not be weakened without an explicit documented decision.

The Terraform apply role uses an explicit baseline action list rather than service-wide wildcard grants. Its Route 53 record changes are restricted to the delegated hosted-zone ARN. Terraform must tag every supported resource with `Project=happy-post` and `Environment=sandbox` so later IAM refinements can restrict mutation by resource tags and ARN.

## Optional services

WAF, Service Connect, blue/green deployment, VPC endpoints, notifications, and end-to-end TLS are disabled by default. They must not be represented as baseline security controls until separately approved and implemented.
