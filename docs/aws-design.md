# Future AWS design — not deployed or implemented

The original plan proposed three ECS Fargate services, RDS, S3, an Application Load Balancer, private subnets, Secrets Manager and CloudWatch. Those services can incur charges. This local milestone creates none of them and contains no deploy workflow or AWS credentials.

Local-to-cloud mapping:

| Local | Future AWS resource |
| --- | --- |
| Nginx + React container | Dashboard ECS service behind an ALB |
| FastAPI container | Private ECS service + ALB path routing |
| Worker container | ECS worker service |
| PostgreSQL volume | Private RDS PostgreSQL |
| PDF shared volume | Private S3 object storage; requires a storage adapter |
| `.env` | Secrets Manager and ECS secret injection |
| Container stdout | CloudWatch logs |

Before any cloud work: implement Terraform modules, a remote-state bootstrap, scoped task roles, secret handling, encryption, logging and teardown documentation. The PDF adapter must change because separate ECS tasks cannot share the local Docker named volume. Replace Nginx's Docker service-name proxy with the cloud routing design. Add migrations rather than relying on metadata creation. Test real PostgreSQL concurrency and migrations before increasing the worker count.

For a strict $0 spending policy, only format, validate and statically scan future Terraform. Do not run `terraform apply`, create an account for this project, or imply an AWS deployment has been verified. Live AWS cost estimates must be researched when a deployment is actually being considered; no current price claim is made here.

## What exists in `infra/` today

Terraform now covers the foundations, not the compute layer:

| Resource | Purpose |
| --- | --- |
| KMS key (rotation on, explicit key policy) | Encrypts the PDF bucket, image registries, logs and the secret |
| Private S3 bucket | Replaces the shared Docker volume: public access blocked, versioned, KMS encrypted, TLS only, 30-day expiry for demo PDFs |
| Two ECR repositories (`api`, `dashboard`) | Immutable tags, scan on push, KMS encrypted, only the last 10 images kept |
| Three CloudWatch log groups | One per service, 365-day retention, KMS encrypted |
| Secrets Manager secret | Holds the JWT secret. The value is set by hand, never in Terraform or Git |
| Two IAM roles | Task role limited to the `pdfs/` prefix of one bucket; execution role limited to reading one secret |

Still to design and build: the S3 storage adapter in the app, ECS Fargate services, RDS PostgreSQL, the load balancer and private networking (the `network` module from the aws-landing-zone-lite project is the starting point), remote state and a teardown guide.

Checks: formatted and validated in CI, scanned by Checkov with reasons for every skip in `.checkov.yaml`. Not applied, so no AWS cost.
