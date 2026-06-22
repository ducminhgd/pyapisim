# Python Simulator APIs

A Mock Server in Python — configure API endpoints with custom status codes, headers,
response bodies, and simulated latency.

## Quick Start (Docker)

```bash
# Build
docker build -t pyapisim:latest .
```

### PostgreSQL

```bash
# 1. Run migrations
docker run --rm --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest python manage.py migrate

# 2. Create a superuser (optional)
docker run --rm -it --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest python manage.py createsuperuser

# 3. Start the server
docker run --rm -p 8000:8000 --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest
```

### MySQL / MariaDB

```bash
# 1. Run migrations
docker run --rm --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest python manage.py migrate

# 2. Create a superuser (optional)
docker run --rm -it --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest python manage.py createsuperuser

# 3. Start the server
docker run --rm -p 8000:8000 --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest
```

### SQLite

```bash
# 1. Create a persistent volume for the database file
docker volume create pyapisim-data

# 2. Run migrations
docker run --rm --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest python manage.py migrate

# 3. Create a superuser (optional)
docker run --rm -it --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest python manage.py createsuperuser

# 4. Start the server
docker run --rm -p 8000:8000 --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest
```

The server listens on `http://localhost:8000`. Mock endpoints are available at
`/mockapi/{collection_code}/{endpoint_path}`.

## Local Development

```bash
# Install dependencies
uv sync

# Setup
cp .env.sample .env      # edit .env with your values
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Run
uv run python manage.py runserver
```

## Managing Mock Endpoints

Open the admin panel at `http://localhost:8000/admin/` and configure:

- **Collections** — group related endpoints (e.g. `users`, `orders`)
- **Endpoints** — set path, HTTP methods, status code, response headers, body, and delay (ms)