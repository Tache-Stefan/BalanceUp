#!/usr/bin/env bash
set -euo pipefail

step() {
  printf '\n==> %s\n' "$1"
}

step "Validate docker-compose.yml"
docker compose config --quiet

step "Ensure containers are running"
docker compose up -d

step "Backend: Black formatting check"
docker compose exec -T backend black --check .

step "Backend: Flake8 lint"
docker compose exec -T backend flake8 .

step "Backend: Pytest"
docker compose exec -T backend pytest

step "Frontend: Prettier formatting check"
docker compose exec -T frontend npm run format:check

step "Frontend: ESLint"
docker compose exec -T frontend npm run lint

step "Frontend: TypeScript typecheck"
docker compose exec -T frontend npm run typecheck

step "Frontend: Vitest"
docker compose exec -T frontend npm test

step "Frontend: Production build"
docker compose exec -T frontend npm run build

printf '\nAll local CI checks passed!\n'
