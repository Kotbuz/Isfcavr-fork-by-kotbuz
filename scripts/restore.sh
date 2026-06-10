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
Usage: $(basename "$0") [dump-file] [uploads-archive]

Restore PostgreSQL from a dump and optionally restore uploads.
If no dump file is provided, the latest db_backup_*.sql file from $BACKUP_DIR is used.
If no uploads archive is provided, the latest uploads_backup_*.tar.gz file is used.
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

if [[ $# -gt 2 ]]; then
  usage
  error "Too many arguments"
fi

DB_DUMP="${1:-}"
UPLOADS_ARCHIVE="${2:-}"

if [[ -z "$DB_DUMP" ]]; then
  DB_DUMP="$(ls -1t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$DB_DUMP" || ! -f "$DB_DUMP" ]]; then
  error "Database dump file not found. Provide a valid dump path or place backups in $BACKUP_DIR."
fi

if [[ -z "$UPLOADS_ARCHIVE" ]]; then
  UPLOADS_ARCHIVE="$(ls -1t "$BACKUP_DIR"/uploads_backup_*.tar.gz 2>/dev/null | head -n 1 || true)"
fi

if [[ -n "$UPLOADS_ARCHIVE" && ! -f "$UPLOADS_ARCHIVE" ]]; then
  error "Uploads archive file not found: $UPLOADS_ARCHIVE"
fi

if [[ -n "$DB_DUMP" ]]; then
  echo "Restoring database from: $DB_DUMP"
  if command -v psql >/dev/null 2>&1; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
SQL
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 < "$DB_DUMP"
  else
    if command -v docker >/dev/null 2>&1; then
      docker compose exec -T -e PGPASSWORD="$DB_PASSWORD" db psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
      docker compose exec -T -e PGPASSWORD="$DB_PASSWORD" db psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 < "$DB_DUMP"
    else
      error "psql is not installed and docker is not available. Cannot restore database."
    fi
  fi
  echo "Database restore completed."
fi

if [[ -n "$UPLOADS_ARCHIVE" ]]; then
  echo "Restoring uploads from: $UPLOADS_ARCHIVE"
  mkdir -p "$UPLOADS_DIR"
  find "$UPLOADS_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  tar -xzf "$UPLOADS_ARCHIVE" -C "$PROJECT_ROOT"
  echo "Uploads restore completed."
else
  echo "No uploads archive provided and no uploads backup found. Skipping uploads restore."
fi

echo "Restore finished successfully."
