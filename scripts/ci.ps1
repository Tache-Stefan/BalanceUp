$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[FAILED] $Label (exit code $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Invoke-Step "Validate docker-compose.yml" {
    docker compose config --quiet
}

Invoke-Step "Ensure containers are running" {
    docker compose up -d
}

Invoke-Step "Backend: Black formatting check" {
    docker compose exec -T backend black --check .
}

Invoke-Step "Backend: Flake8 lint" {
    docker compose exec -T backend flake8 .
}

Invoke-Step "Backend: Pytest" {
    docker compose exec -T backend pytest
}

Invoke-Step "Frontend: Prettier formatting check" {
    docker compose exec -T frontend npm run format:check
}

Invoke-Step "Frontend: ESLint" {
    docker compose exec -T frontend npm run lint
}

Invoke-Step "Frontend: TypeScript typecheck" {
    docker compose exec -T frontend npm run typecheck
}

Invoke-Step "Frontend: Vitest" {
    docker compose exec -T frontend npm test
}

Invoke-Step "Frontend: Production build" {
    docker compose exec -T frontend npm run build
}

Write-Host "`nAll local CI checks passed!" -ForegroundColor Green
