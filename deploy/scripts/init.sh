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

set -a
. ./.env
set +a

sh "$SCRIPT_DIR/render-xbt-config.sh"
docker compose pull
docker compose up -d mysql redis

echo "Waiting for MySQL to become ready..."
until docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent >/dev/null 2>&1; do
  sleep 2
done

XBT_TABLE_EXISTS=$(docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -uroot -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DATABASE}' AND table_name='xbt_users';")

if [ "$XBT_TABLE_EXISTS" = "0" ]; then
  echo "Importing XBT schema into MySQL..."
  docker compose run --rm --entrypoint cat xbt /usr/local/share/xbt/xbt_tracker.sql \
    | docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -uroot "$MYSQL_DATABASE"
fi

XBT_CAN_LEECH_EXISTS=$(docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -uroot -Nse "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='${MYSQL_DATABASE}' AND table_name='xbt_users' AND column_name='can_leech';")

if [ "$XBT_CAN_LEECH_EXISTS" = "0" ]; then
  echo "Adding missing xbt_users.can_leech column..."
  docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -uroot "$MYSQL_DATABASE" -e "ALTER TABLE xbt_users ADD COLUMN can_leech TINYINT(1) NOT NULL DEFAULT 1 AFTER torrent_pass;"
fi

docker compose up -d backend frontend xbt nginx

echo "Run 'docker compose -f deploy/docker-compose.yml exec backend python manage.py createsuperuser' to create the first admin user."
