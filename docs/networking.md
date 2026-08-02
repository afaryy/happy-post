# Networking

![AWS sandbox runtime architecture](diagrams/aws-ecs-runtime-architecture.drawio.svg)

Happy Post runs in one sandbox VPC spanning two Availability Zones. Each zone contains a public subnet, private application subnet, and private database subnet. The internet-facing HTTPS ALB spans the public subnets. ECS Fargate tasks run only in private application subnets, and RDS PostgreSQL uses a private DB subnet group across the database subnets.

The Internet Gateway serves the public ALB and the one sandbox NAT Gateway. Private application tasks use the NAT Gateway for approved outbound ECR, CloudWatch, and external-dependency access. RDS has no public IP and no public route.

Security groups enforce this path: Internet to ALB on TCP 80 only for HTTP-to-HTTPS redirect and on HTTPS 443 for application traffic; ALB to frontend and backend task security groups on their application ports; backend task security group to RDS on TCP 5432. The frontend and ALB have no direct path to RDS.

Route 53, ACM, ECR, Secrets Manager, and CloudWatch are regional managed services outside the VPC. API Gateway, CloudFront, VPC endpoints, and end-to-end TLS are not current-baseline components.

The applied network Terraform root is [`infra/terraform/foundations/network`](../infra/terraform/foundations/network). It configures the approved remote state key, enforces the documented route boundaries, and uses separate security-group rule resources to avoid cyclic dependencies between the ALB and service security groups. Its pending HTTP ingress reconciliation must be applied before the edge root. The separate [`stacks/data`](../infra/terraform/stacks/data) root consumes only the private database subnet IDs and database security-group ID from that network state.
