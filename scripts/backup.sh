#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_DIR="$PROJECT_ROOT/backups"
UPLOADS_DIR="$PROJECT_ROOT/uploads"

function error() {
  echo "ERROR: $*" >&2
  exit 1
}

function usage() {
  cat <<EOF
Usage: $(basename "$0")

Create a PostgreSQL dump and archive the uploads directory.
If pg_dump is available on the host, it is used. Otherwise the script falls back to docker compose exec.

The script reads database credentials from $ENV_FILE.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -f "$ENV_FILE" ]]; then
  error "Missing .env file at $ENV_FILE"
fi

set -a
source "$ENV_FILE"
set +a

: "${DB_NAME:?DB_NAME is required in .env}"
: "${DB_USER:?DB_USER is required in .env}"
: "${DB_PASSWORD:?DB_PASSWORD is required in .env}"
: "${DB_HOST:?DB_HOST is required in .env}"
: "${DB_PORT:?DB_PORT is required in .env}"

export PGPASSWORD="$DB_PASSWORD"
mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DB_DUMP="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
UPLOADS_ARCHIVE="$BACKUP_DIR/uploads_backup_${TIMESTAMP}.tar.gz"

echo "Backup directory: $BACKUP_DIR"
echo "Creating database dump: $DB_DUMP"

default_pg_dump() {
  pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F p -f "$DB_DUMP" "$DB_NAME"
}

if command -v pg_dump >/dev/null 2>&1; then
  default_pg_dump
else
  if command -v docker >/dev/null 2>&1; then
    docker compose exec -T -e PGPASSWORD="$DB_PASSWORD" db pg_dump -U "$DB_USER" -F p "$DB_NAME" > "$DB_DUMP"
  else
    error "pg_dump is not installed and docker is not available. Cannot create database backup."
  fi
fi

echo "Database backup completed."

if [[ -d "$UPLOADS_DIR" ]]; then
  echo "Archiving uploads directory: $UPLOADS_DIR"
  tar -czf "$UPLOADS_ARCHIVE" -C "$PROJECT_ROOT" "$(basename "$UPLOADS_DIR")"
  echo "Uploads archive completed."
else
  echo "Warning: uploads directory not found at $UPLOADS_DIR. Skipping uploads backup."
fi

echo "Backup finished successfully."
