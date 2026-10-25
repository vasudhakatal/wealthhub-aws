$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (!(Test-Path .env)) {
    $bytes = New-Object byte[] 48
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $secret = [Convert]::ToBase64String($bytes)
    $rng.Dispose()
    "JWT_SECRET=$secret`nDEMO_PASSWORD=local-demo-only" | Set-Content -Encoding ascii .env
    Write-Host "Created local configuration. Demo login: demo / local-demo-only"
} else { Write-Host "Keeping your existing .env configuration." }
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Docker startup failed. Check Docker Desktop and the output above." }
Write-Host "Open http://localhost:18080 after the containers finish starting."
