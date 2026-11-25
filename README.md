# BalanceUp

## Local Development (Docker Compose)

1. Copy the example environment file (optional; `docker-compose.yml` also provides development defaults):

   ```bash
   cp .env.example .env
   ```

2. Build and start PostgreSQL, FastAPI backend, and React frontend:

   ```bash
   docker compose up -d --build
   ```

   - Frontend: http://localhost:5173
   - Backend API docs: http://localhost:8000/docs
   - Healthcheck: http://localhost:8000/api/v1/health

   On first startup, PostgreSQL automatically executes SQL scripts in [`db/`](db/) (currently [`db/01_schema.sql`](db/01_schema.sql)) inside `/docker-entrypoint-initdb.d`.

3. Verify containers:

   ```bash
   docker compose ps
   docker compose exec db psql -U balanceup -d BalanceUp -c "\dt"
   docker compose exec backend pytest
   docker compose exec frontend npm test
   ```

4. Stop or reset the stack:

   ```bash
   # Stop containers (keeps DB data volume)
   docker compose down

   # Stop containers and wipe DB data volume to re-run init scripts
   docker compose down -v
   ```

## Backend Local Tooling (`uv`)

Run commands inside `backend/`:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run alembic current
```

## Database Migrations (Alembic)

Alembic is configured in [`backend/alembic.ini`](backend/alembic.ini) and [`backend/alembic/env.py`](backend/alembic/env.py), reading `DATABASE_URL` from application settings (root [`.env`](.env) locally or container environment variables in Docker) and `Base.metadata` from [`backend/app/models/__init__.py`](backend/app/models/__init__.py).

When adding or updating the 14 SQLAlchemy ORM models:

1. Import all ORM model classes in [`backend/app/models/__init__.py`](backend/app/models/__init__.py) so `Base.metadata` discovers them.
2. Generate a migration (formatted automatically with `black` via `post_write_hooks`):

   ```bash
   # From backend/ (or via `docker compose exec backend ...`)
   alembic revision --autogenerate -m "create initial schema"
   ```

3. Review the generated script in `backend/alembic/versions/` — PostgreSQL views (such as `v_user_points` in [`db/01_schema.sql`](db/01_schema.sql)) and some partial/expression indexes must be added or verified manually.
4. Apply migrations:

   ```bash
   alembic upgrade head
   ```

> [!NOTE]
> On first startup, `docker compose up` initializes PostgreSQL using [`db/01_schema.sql`](db/01_schema.sql) without creating an `alembic_version` table. If running against a database already initialized by `01_schema.sql`, align it with `alembic stamp head` (or reset with `docker compose down -v` once migrations manage the full schema).

## Frontend Local Tooling (`npm`)

Run commands inside `frontend/`:

```bash
cd frontend
npm install
npm run dev
npm run lint
npm run typecheck
npm test
```

## CI (GitHub Actions)

Pull requests and pushes to `main` and `develop` automatically run [`.github/workflows/ci.yml`](.github/workflows/ci.yml), checking:
- **Backend:** `black --check`, `flake8`, and `pytest` (with PostgreSQL 17 service)
- **Frontend:** `prettier --check`, `eslint`, `tsc -b --noEmit`, `vitest run`, and `vite build`
- **Compose:** `docker compose config --quiet`

Run the same checks locally before pushing:

```powershell
# Windows (PowerShell)
.\scripts\ci.ps1
```

```bash
# macOS / Linux / Git Bash
bash scripts/ci.sh
```
