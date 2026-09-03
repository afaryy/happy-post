# Sandbox Destroy Runbook

Use this runbook to temporarily remove the Happy Post AWS sandbox and stop the
Terraform-managed runtime charges. The procedure keeps the CloudFormation
bootstrap resources so that the sandbox can be deployed again later.

## Scope and safety rules

- Run this only when the sandbox application is not needed.
- The procedure deletes the deployed ECS services, ALB, RDS database, VPC, and
  related Terraform-managed resources.
- The RDS destroy step creates a final database snapshot. Keep it only if the
  database data must be recoverable; otherwise delete it after the destroy.
- Do **not** delete the CloudFormation bootstrap stack, Terraform state S3
  bucket, or DynamoDB lock table. They are required for a future Terraform
  deployment.
- Complete each workflow run successfully before starting the next target.

## Prerequisites

1. Confirm that the application can be unavailable.
2. Export any database data that must be retained, if a database snapshot is not
   sufficient for the required recovery process.
3. Ensure you have permission to dispatch GitHub Actions workflows for this
   repository and to view the `sandbox` environment deployment.
4. Open the repository on GitHub and go to **Actions**.

## Run the Terraform Destroy workflow

For every target below:

1. In **Actions**, select the **Terraform Destroy** workflow.
2. Select **Run workflow** and leave the branch set to `main`.
3. Select the required `target` value.
4. Enter the exact matching `confirm` value shown below.
5. Confirm that the selected target is the next item in the required destroy
   order, then select **Run workflow**.
6. Wait until the workflow succeeds before proceeding to the next target.

The workflow creates and applies the fresh destroy plan in the same run; it does
not pause for an approval after the plan is created. Review the completed plan
and apply output before starting the next target. If the selected target is
wrong, cancel the run immediately and investigate before dispatching another
destroy.

## Required destroy order

### 1. Backend service

| Workflow input | Value |
| --- | --- |
| `target` | `backend-service` |
| `confirm` | `destroy-backend-service` |

This removes the backend ECS Fargate service and its service-specific resources.

### 2. Frontend service

| Workflow input | Value |
| --- | --- |
| `target` | `frontend-service` |
| `confirm` | `destroy-frontend-service` |

This removes the frontend ECS Fargate service and its service-specific resources.

### 3. Edge

| Workflow input | Value |
| --- | --- |
| `target` | `edge` |
| `confirm` | `destroy-edge` |

This removes the public Application Load Balancer, listeners, target groups, ACM
validation records, and the Route 53 alias managed by this stack.

### 4. Platform

| Workflow input | Value |
| --- | --- |
| `target` | `platform` |
| `confirm` | `destroy-platform` |

This removes the ECS cluster, ECR repositories, CloudWatch log groups, and
Terraform-managed runtime IAM roles. Do not run this before both service targets
have been removed.

### 5. Data

| Workflow input | Value |
| --- | --- |
| `target` | `data` |
| `confirm` | `destroy-data` |

This removes the RDS instance and database credentials secret. It creates an RDS
final snapshot with a generated suffix. Record the snapshot identifier if the
database must be restored later.

### 6. Network

| Workflow input | Value |
| --- | --- |
| `target` | `network` |
| `confirm` | `destroy-network` |

This removes the NAT Gateway, Elastic IP address, VPC, subnets, route tables,
internet gateway, and security groups. Run it only after the service, edge, and
data stacks have completed successfully.

### 7. Observability (only if applied)

| Workflow input | Value |
| --- | --- |
| `target` | `observability` |
| `confirm` | `destroy-observability` |

Run this only if the observability stack exists in the deployed environment.

## Manual cleanup after Terraform destroy

1. In the AWS Console, open **RDS** → **Snapshots** and find the final snapshot
   created by the `data` destroy. Delete it only when its data is no longer
   needed. A retained snapshot continues to incur storage charges.
2. In **Billing and Cost Management** → **Cost Explorer**, verify that new
   charges for ECS, EC2, RDS, ELB, and VPC stop appearing after billing data has
   refreshed.
3. If charges remain, inspect the AWS Console for resources that may predate or
   sit outside this Terraform state, especially NAT Gateways, unattached Elastic
   IP addresses, EBS volumes or snapshots, load balancers, and EKS resources.
   Delete only resources that have been confirmed as unused.

## Resources to retain

Keep the CloudFormation bootstrap stack and its retained resources:

- Terraform state bucket: `happy-post-tfstate-893794041695-ap-southeast-2`
- Terraform lock table: `happy-post-sandbox-terraform-lock`
- Bootstrap-managed permissions boundary and GitHub OIDC roles

These resources support the next Terraform deployment. The lock table is
deletion-protected, and the state bucket is versioned and retained by design.

## Restore the sandbox later

To recreate the sandbox, run the Terraform apply workflow in dependency order:

1. `network`
2. `data`
3. `platform`
4. `edge`
5. Publish the frontend and backend images.
6. Bootstrap `backend-service` and `frontend-service` with verified image
   digests.
7. Use the ECS deployment workflow for subsequent image revisions.

The original RDS data is available only if its final snapshot was retained. A
new `data` apply otherwise creates a fresh database and credentials secret.
