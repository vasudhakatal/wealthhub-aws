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
