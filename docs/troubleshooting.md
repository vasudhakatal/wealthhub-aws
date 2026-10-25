# Troubleshooting

[Back to README](../README.md)

## Setup script does not exist

The terminal is in an outer extraction folder. Run `dir`. Open the inner `wealthhub-aws` folder until `docker-compose.yml`, `README.md` and `scripts` appear. Run the setup command there.

## Windows blocks the dashboard port

The first manual run failed on port 8080 with a socket access-permissions error. Port 18080 worked and is now the default. If 18080 is also blocked, choose another available port and change only the host side of the dashboard mapping, e.g. `127.0.0.1:18081:80`. Then run `docker compose up -d` and open that host port. Do not remove Windows port reservations or disable security controls just to run this demo.

For the smoke script on another port:

```powershell
$env:WEALTHHUB_URL = "http://localhost:18081"
python scripts/smoke.py
```

## Containers fail to start

Ensure Docker Desktop's Linux engine is running. From this project folder:

```powershell
docker compose ps
docker compose logs --tail 100 api worker dashboard db
```

Share the error text if troubleshooting is needed. Do not share `.env` contents or tokens.

## PDF is queued or failed

The worker polls for jobs. Wait a few seconds, then inspect `docker compose logs --tail 100 worker`. A failed job has no retry button in this version; fix the underlying issue and submit another fictional profile. Do not delete the database as a first troubleshooting step.

## Login fails

Default credentials are `demo` / `local-demo-only`. If `.env` has a custom `DEMO_PASSWORD`, use that instead. The UI prefill is the original value. After too many login attempts, wait one minute. Tokens expire after one hour; sign in again.

## Changes do not appear

Changes to packaged application code require `docker compose up --build -d`. A README-only change does not need a container rebuild.
