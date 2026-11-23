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
