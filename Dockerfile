# syntax=docker/dockerfile:1

# ---- build stage ----
FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install MariaDB client dev libraries (needed to compile mysqlclient)
USER root
RUN apk update && apk add mariadb-connector-c-dev
USER nonroot

# Install dependencies (layer cache: only re-install when lockfile changes)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and collect static files
COPY . .
ENV SECRET_KEY=dummy STATIC_ROOT=/app/staticfiles
RUN uv run --frozen python manage.py collectstatic --noinput

# ---- runtime stage ----
FROM cgr.dev/chainguard/python:latest

WORKDIR /app

# Copy virtual env and static files from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/staticfiles /app/staticfiles
ENV PATH="/app/.venv/bin:$PATH"

# Copy MariaDB client shared library (needed at runtime by mysqlclient)
COPY --from=builder /usr/lib/libmariadb.so.3 /usr/lib/
COPY --from=builder /usr/lib/mariadb/plugin /usr/lib/mariadb/plugin

# Copy application code
COPY . .

EXPOSE 8000

ENTRYPOINT []
CMD ["gunicorn", "pyapisim.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
