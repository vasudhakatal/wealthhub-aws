#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  umask 077
  printf 'JWT_SECRET=%s\nDEMO_PASSWORD=local-demo-only\n' "$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" > .env
fi
docker compose up --build -d
