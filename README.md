# Python Simulator APIs

A Mock Server in Python — configure API endpoints with custom status codes, headers,
response bodies, and simulated latency.

## Features

- **Mock endpoints** — define path, HTTP methods, status code, headers, body, and
  simulated delay (ms) per endpoint.
- **Collections** — group related endpoints with a unique code. Each collection
  gets its own URL prefix: `/mockapi/{code}/{path}`.
- **Sharing** — share a collection with other users as Viewer (read-only) or
  Editor (modify endpoints, cannot delete). Only the owner can delete endpoints
  or the collection.
- **Admin panel** — manage everything via a modern Django admin UI
  ([django-unfold](https://github.com/unfoldadmin/django-unfold)).

---

## Quick Start — Docker Compose (recommended)

```bash
# 1. Create env file from the example
cp .env.example .env
# edit .env — set SECRET_KEY, ALLOWED_HOSTS, and pick a DB backend

# 2. Create host directories for persistent data
mkdir -p $HOME/docker-volumes/pyapisim/{data,static}

# 3. Start (SQLite by default — zero extra dependencies)
docker compose up -d --build

# 4. Run migrations
docker compose exec app python manage.py migrate

# 5. Create a superuser
docker compose exec app python manage.py createsuperuser
```

Open `http://localhost:8000/admin/` and log in.

### Switching to PostgreSQL

```bash
# Create the data directory
mkdir -p $HOME/docker-volumes/pyapisim/pgdata

# Edit .env — uncomment the PostgreSQL block and set DB_ENGINE=postgresql
docker compose --profile postgres up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

### Switching to MariaDB / MySQL

```bash
# Create the data directory
mkdir -p $HOME/docker-volumes/pyapisim/mariadbdata

# Edit .env — uncomment the MariaDB block and set DB_ENGINE=mariadb
docker compose --profile mariadb up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

---

## Quick Start — Docker (`docker run`)

### Build the image

```bash
docker build -t pyapisim:latest .
```

### SQLite (with a named volume for persistence)

```bash
docker volume create pyapisim-data

# Migrations
docker run --rm --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest python manage.py migrate

# Create superuser
docker run --rm -it --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest python manage.py createsuperuser

# Start server
docker run --rm -p 8000:8000 --env-file .env \
  -v pyapisim-data:/app/data \
  -e DB_NAME=/app/data/db.sqlite3 \
  pyapisim:latest
```

### PostgreSQL

```bash
# Migrations
docker run --rm --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest python manage.py migrate

# Create superuser
docker run --rm -it --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest python manage.py createsuperuser

# Start server
docker run --rm -p 8000:8000 --env-file .env \
  -e DB_ENGINE=postgresql \
  pyapisim:latest
```

### MariaDB / MySQL

```bash
# Migrations
docker run --rm --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest python manage.py migrate

# Create superuser
docker run --rm -it --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest python manage.py createsuperuser

# Start server
docker run --rm -p 8000:8000 --env-file .env \
  -e DB_ENGINE=mariadb \
  pyapisim:latest
```

---

## Quick Start — CLI (local development)

```bash
# Install dependencies
uv sync

# Setup
cp .env.example .env      # edit .env with your values
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Run
uv run python manage.py runserver
```

---

## Managing Mock Endpoints

Open the admin panel at `http://localhost:8000/admin/` and configure:

- **Collections** — group related endpoints (e.g. `users`, `orders`). Each
  collection has a unique `code` that becomes part of the mock URL.
- **Endpoints** — set path, HTTP methods, status code, response headers, body,
  and delay (ms). Each endpoint belongs to a collection.

Mock endpoints are served at:

```
/mockapi/{collection_code}/{endpoint_path}
```

### Example

| Collection code | Endpoint path | Mock URL |
|---|---|---|
| `users` | `list` | `/mockapi/users/list` |
| `users` | `detail/42` | `/mockapi/users/detail/42` |
| `orders` | `create` | `/mockapi/orders/create` |
