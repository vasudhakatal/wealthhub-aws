# Local security decisions

- A single demo adviser authenticates with a local configured password. All protected endpoints share this identity; this is not multi-tenant access control.
- One-hour HS256 JWTs validate signature, issuer, audience and expiry. Tokens remain in memory, not localStorage.
- Secrets are generated locally and excluded from source control/build context. Restarting an unconfigured non-Compose API changes its fallback signing secret.
- Rate limits are per-process and keyed by the immediate peer. Behind Nginx all browser requests share its address; appropriate for a one-person demo, not public traffic.
- The dashboard binds only `127.0.0.1:18080`. PostgreSQL and API have no published host ports.
- Onboarding risk is an enum. Names and email are bounded and validated; XML-sensitive characters are escaped in ReportLab paragraphs. SQLAlchemy uses bound parameters.
- PDF paths derive from server-generated job UUIDs. The API checks job state and authenticates before returning the file.
- Local volumes are not application-encrypted; host security protects them. API/worker run as a non-root user. Nginx/PostgreSQL use upstream defaults.
- Audit logs record request ID, method, path and status, not form bodies or access tokens. This is not compliance-grade auditing.
- CI uses read-only repository permissions and performs no cloud deployment. GitHub Actions major-version tags are not immutable SHA pins; harden those in the next CI pass.

Production gaps: identity provider, per-user authorization, TLS, distributed rate limiting, managed secrets, migrations, backups, retention controls and independent security review.
