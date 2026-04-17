#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPLOY_DIR=$(dirname "$SCRIPT_DIR")

cd "$DEPLOY_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created deploy/.env. Edit it and rerun deploy/scripts/init.sh." >&2
  exit 1
fi

docker compose pull
docker compose up -d mysql redis

echo "Waiting for MySQL to become ready..."
until docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent >/dev/null 2>&1; do
  sleep 2
done

docker compose up -d backend frontend nginx

echo "Run 'docker compose -f deploy/docker-compose.yml exec backend python manage.py createsuperuser' to create the first admin user."
