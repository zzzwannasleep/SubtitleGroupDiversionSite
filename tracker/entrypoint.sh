#!/bin/sh
set -eu

CONFIG_FILE="${XBT_CONFIG_FILE:-/etc/xbt/xbt_tracker.conf}"
DB_HOST="${XBT_DB_HOST:-${MYSQL_HOST:-mysql}}"
DB_PORT="${XBT_DB_PORT:-${MYSQL_PORT:-3306}}"
DB_NAME="${XBT_DB_NAME:-${MYSQL_DATABASE:-}}"
DB_USER="${XBT_DB_USER:-${MYSQL_USER:-}}"
DB_PASSWORD="${XBT_DB_PASSWORD:-${MYSQL_PASSWORD:-}}"
TRACKER_PORT="${XBT_TRACKER_PORT:-2710}"
SCHEMA_FILE="${XBT_SCHEMA_FILE:-/usr/local/share/xbt/xbt_tracker.sql}"

render_config() {
  mkdir -p "$(dirname "$CONFIG_FILE")"

  cat > "$CONFIG_FILE" <<EOF
mysql_host = ${DB_HOST}
mysql_user = ${DB_USER}
mysql_password = ${DB_PASSWORD}
mysql_database = ${DB_NAME}
announce_interval = 1800
anonymous_connect = 0
anonymous_announce = 0
anonymous_scrape = 0
auto_register = 0
daemon = 0
debug = 0
full_scrape = 0
gzip_debug = 1
gzip_scrape = 1
listen_ipa = *
listen_port = ${TRACKER_PORT}
log_access = 0
log_announce = 0
log_scrape = 0
pid_file = /tmp/xbt_tracker.pid
read_config_interval = 60
read_db_interval = 60
scrape_interval = 0
table_announce_log = xbt_announce_log
table_files = xbt_files
table_files_users = xbt_files_users
table_scrape_log = xbt_scrape_log
table_users = xbt_users
write_db_interval = 15
EOF
}

wait_for_mysql() {
  echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
  until MYSQL_PWD="$DB_PASSWORD" mysqladmin ping \
    -h "$DB_HOST" \
    -P "$DB_PORT" \
    -u"$DB_USER" \
    --silent >/dev/null 2>&1; do
    sleep 2
  done
}

ensure_schema() {
  XBT_USERS_EXISTS=$(
    MYSQL_PWD="$DB_PASSWORD" mysql \
      -h "$DB_HOST" \
      -P "$DB_PORT" \
      -u"$DB_USER" \
      "$DB_NAME" \
      -Nse "SHOW TABLES LIKE 'xbt_users';"
  )

  XBT_FILES_EXISTS=$(
    MYSQL_PWD="$DB_PASSWORD" mysql \
      -h "$DB_HOST" \
      -P "$DB_PORT" \
      -u"$DB_USER" \
      "$DB_NAME" \
      -Nse "SHOW TABLES LIKE 'xbt_files';"
  )

  if [ -z "$XBT_USERS_EXISTS" ] || [ -z "$XBT_FILES_EXISTS" ]; then
    echo "Importing XBT schema into ${DB_NAME}..."
    MYSQL_PWD="$DB_PASSWORD" mysql \
      -h "$DB_HOST" \
      -P "$DB_PORT" \
      -u"$DB_USER" \
      "$DB_NAME" < "$SCHEMA_FILE"
  fi
}

if [ -n "$DB_NAME" ] || [ -n "$DB_USER" ] || [ -n "$DB_PASSWORD" ]; then
  : "${DB_NAME:?XBT_DB_NAME or MYSQL_DATABASE is required}"
  : "${DB_USER:?XBT_DB_USER or MYSQL_USER is required}"
  : "${DB_PASSWORD:?XBT_DB_PASSWORD or MYSQL_PASSWORD is required}"
  : "${TRACKER_PORT:?XBT_TRACKER_PORT is required}"

  render_config
  wait_for_mysql
  ensure_schema
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing tracker config: $CONFIG_FILE" >&2
  exit 1
fi

cd "$(dirname "$CONFIG_FILE")"
exec /usr/local/bin/xbt_tracker
