# Project status and roadmap

[Back to README](../README.md)

## Implemented

- [x] Synthetic bank, shares and super connectors with timeout/retry tests.
- [x] Portfolio API, JWT demo login and protected routes.
- [x] React holdings, allocation and sample performance charts.
- [x] Validated onboarding and database-backed jobs.
- [x] Worker-generated PDFs and authenticated download.
- [x] Windows Docker startup and manual onboarding/PDF demonstration.
- [x] Backend tests, Python lint, UI build and dependency audit checked during development.
- [x] CI workflow with tests, lint, UI build, Compose integration, gitleaks, Trivy and Terraform checks.
- [x] 40 automated tests across authentication, resilience, validation, rate limiting and the worker.
- [x] Terraform for AWS foundations (KMS, private S3 bucket, ECR, logs, IAM roles, secret container), statically scanned with Checkov, not applied.

## Next: public portfolio evidence

- [ ] Push the repository and review actual CI results.
- [ ] Add a CI badge after a successful run.
- [ ] Add a full portfolio overview screenshot and short demo video.
- [ ] Run the script-based smoke check against Windows Compose.
- [ ] Add browser tests and check desktop/mobile accessibility.

## Later: hardening

- [ ] Schema migrations and repeatable seed data.
- [ ] Job retries, attempts, leases and submission idempotency.
- [ ] Test concurrent workers on real PostgreSQL.
- [ ] Split the React UI into focused modules and improve chart loading/bundle size.
- [ ] Pin CI actions and base images by reviewed immutable digests.

## Cloud extension — no paid resources without a new budget decision

- [ ] Add the S3 PDF-storage adapter.
- [ ] Document IAM, secret injection, observability and teardown.
- [ ] Research costs only if deployment is considered in future.

No Terraform code or AWS deployment is included in the current version. Static validation would not prove that a future deployment works.
