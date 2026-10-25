# Verification record

Development environment: Linux with Python 3.12 and Node 24. Windows and Docker engine execution are not available here.

Results are recorded at packaging time. Backend tests use an isolated SQLite database to exercise routes and PDF processing. PostgreSQL-specific row locking and Docker volume permissions require the Compose smoke check and CI integration job; SQLite tests do not prove these properties.

The delivered GitHub workflow includes a real PostgreSQL Compose integration job but has not yet run in the user's account. The package does not claim cloud deployment, container image scanning or Terraform validation.

## Completed checks

- Seven pytest tests passed: login and protected routes, expired JWTs, independent source failure, timeout retries, onboarding to a valid PDF, invalid inputs and login throttling.
- Ruff checks passed for the API and worker.
- Vite production build passed. Bundler emitted advisory warnings about chart bundle size and dependency `use client` directives; neither blocked the build.
- `npm audit --audit-level=high`: zero reported vulnerabilities at packaging time.
- Multi-process HTTP smoke check passed with the real API, worker and Vite proxy, using SQLite as the local test database: health, dashboard HTML, login, portfolio, persistent job, worker completion and authenticated PDF download.
- Browser visual/interaction testing could not run because Chromium could not create its required process socket in this execution environment. Responsive CSS is included but has not been visually verified.

## Must still verify on Windows / GitHub

- `docker compose` builds all images, starts PostgreSQL, and mounts the PDF volume with the expected permissions.
- Run `python scripts/smoke.py` against the Compose stack to verify the real PostgreSQL path.
- Manually check dashboard charts, narrow-screen layout, onboarding and download in Chrome/Edge.
- Push to GitHub and confirm all included CI jobs pass; do not claim a green pipeline beforehand.


## Subsequent manual Windows verification

The owner supplied screenshots showing PostgreSQL and API healthy, worker running, and dashboard started after changing the blocked host port from 8080 to 18080. The local UI then showed Taylor Demo's job completed, and the generated welcome PDF opened with the expected name, email and Balanced risk profile. This supports a successful single-worker PostgreSQL onboarding flow and PDF download on that machine.

This does not prove concurrent-worker locking, a clean-machine installation, all browser layouts, or a successful GitHub Actions run. Those remain separate checks.
