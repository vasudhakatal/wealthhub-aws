# Engineering decisions

[Back to README](../README.md)

## Database-backed jobs

**Choice:** use the existing PostgreSQL database as the local jobs queue.

**Reason:** one fewer service to configure and an atomic transaction for client/job creation. The worker claims work with `FOR UPDATE SKIP LOCKED`, which prevents concurrent PostgreSQL consumers from claiming the same row while the lock is held.

**Trade-off:** a transaction stays open during PDF generation. That is acceptable for a small local example; long jobs would need short claims, leases, attempts, idempotency and recovery policies, or a dedicated queue. SQLite unit tests do not prove PostgreSQL row locking. The Windows manual run demonstrated one worker, not concurrent-worker stress behaviour.

## FastAPI and explicit validation

FastAPI provides request schemas and generated API documentation. Pydantic constrains fields and risk labels; SQLAlchemy separates persistence from route input. Demo authentication keeps the scope manageable, but a production design needs managed identity and per-user authorization.

## React with same-origin API routing

React renders portfolio charts and form/job state. Nginx serves the built UI and forwards API requests. This gives the browser one entry point and avoids publishing the API/database directly. Client tokens stay in memory; reloading requires login again. That is simple but not a complete production session design.

## Synthetic, failure-aware connectors

Mock sources keep the project reproducible and remove paid API/key requirements. Connector calls are concurrent, bounded and independent. Returning explicit source status makes missing data visible rather than silently presenting a complete portfolio. The current UI's six-month history remains a fixed sample even if a current source fails.

## Local-first, with cloud work separate

The owner required no cloud spending. Compose demonstrates the whole request path on existing hardware. AWS deployment and Terraform are intentionally unimplemented, and no deployment claim is made. Moving to ECS would require more than copying containers: in particular, shared local PDF storage needs an S3 adapter, plus secrets, networking, logging, migrations and deployment validation.

## What to improve next

Add migrations, a storage interface, failed-job retry controls, idempotency keys, concurrency tests, frontend/browser tests, distributed throttling if publicly exposed, and pinned action/container digests. Keep these separate from claims about the current version.
