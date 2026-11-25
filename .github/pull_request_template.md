## Summary
<!-- Briefly describe what this PR changes and why. -->

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor / chore
- [ ] Documentation
- [ ] CI / build / Docker configuration

## Affected Areas
- [ ] Backend (`backend/`)
- [ ] Frontend (`frontend/`)
- [ ] Database / Migrations (`db/`, `backend/alembic/`)
- [ ] Docker / Infrastructure (`docker-compose.yml`, `.github/`)

## How Has This Been Tested?
<!-- Describe the tests or manual verification performed. -->
- [ ] Ran local CI checks (`.\scripts\ci.ps1` or `bash scripts/ci.sh`)
- [ ] Backend: `black --check .`, `flake8 .`, `pytest`
- [ ] Frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`
- [ ] Docker Compose: `docker compose config --quiet`

## Checklist
- [ ] My code follows the project formatting and lint rules
- [ ] I have added or updated tests for my changes (where applicable)
- [ ] I have updated documentation / `.env.example` if needed (no secrets committed)
- [ ] Self-review completed
