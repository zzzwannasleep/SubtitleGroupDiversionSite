#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPLOY_DIR=$(dirname "$SCRIPT_DIR")
ENV_FILE="$DEPLOY_DIR/.env"
TARGET_FILE="$DEPLOY_DIR/xbt/xbt_tracker.conf"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Copy deploy/.env.example to deploy/.env first." >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

: "${MYSQL_DATABASE:?MYSQL_DATABASE is required}"
: "${MYSQL_USER:?MYSQL_USER is required}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"
: "${XBT_TRACKER_PORT:?XBT_TRACKER_PORT is required}"

mkdir -p "$(dirname "$TARGET_FILE")"

cat > "$TARGET_FILE" <<EOF
mysql_host = mysql
mysql_user = ${MYSQL_USER}
mysql_password = ${MYSQL_PASSWORD}
mysql_database = ${MYSQL_DATABASE}
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
listen_port = ${XBT_TRACKER_PORT}
log_access = 0
log_announce = 0
log_scrape = 0
pid_file = /tmp/xbt_tracker.pid
read_config_interval = 60
read_db_interval = 60
scrape_interval = 0
table_announce_log = xbt_announce_log
table_files = xbt_torrents
table_files_users = xbt_peers
table_scrape_log = xbt_scrape_log
table_users = xbt_users
write_db_interval = 15
EOF

echo "Rendered $TARGET_FILE"
