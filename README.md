# BalanceUp

## Database Setup (Docker Compose)

1. Copy the example environment file (optional; `docker-compose.yml` also provides development defaults):

   ```bash
   cp .env.example .env
   ```

2. Start PostgreSQL:

   ```bash
   docker compose up -d
   ```

   On first startup, PostgreSQL automatically executes all SQL scripts in [`db/`](db/) (currently [`db/01_schema.sql`](db/01_schema.sql)) inside `/docker-entrypoint-initdb.d`.

3. Verify the container and schema:

   ```bash
   docker compose ps
   docker compose exec db psql -U balanceup -d BalanceUp -c "\dt"
   ```

4. Stop or reset the database:

   ```bash
   # Stop container (keeps data volume)
   docker compose down

   # Stop container and wipe data volume to re-run init scripts
   docker compose down -v
   ```
