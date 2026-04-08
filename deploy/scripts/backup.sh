#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPLOY_DIR=$(dirname "$SCRIPT_DIR")
BACKUP_DIR="$DEPLOY_DIR/backups"

cd "$DEPLOY_DIR"

if [ ! -f .env ]; then
  echo "Missing deploy/.env. Copy deploy/.env.example to deploy/.env first." >&2
  exit 1
fi

set -a
. ./.env
set +a

: "${MYSQL_DATABASE:?MYSQL_DATABASE is required}"
: "${MYSQL_USER:?MYSQL_USER is required}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

mkdir -p "$BACKUP_DIR"
OUTPUT_FILE="$BACKUP_DIR/mysql-$(date +%Y%m%d-%H%M%S).sql.gz"

docker compose exec -T -e MYSQL_PWD="$MYSQL_PASSWORD" mysql mysqldump -u"$MYSQL_USER" "$MYSQL_DATABASE" | gzip > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
