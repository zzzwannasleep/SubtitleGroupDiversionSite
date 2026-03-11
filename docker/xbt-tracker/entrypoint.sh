#!/bin/sh
set -eu

export XBT_MYSQL_HOST="${XBT_MYSQL_HOST:-tracker-db}"
export XBT_MYSQL_PORT="${XBT_MYSQL_PORT:-3306}"
export XBT_MYSQL_DATABASE="${XBT_MYSQL_DATABASE:-xbt}"
export XBT_MYSQL_USER="${XBT_MYSQL_USER:-tracker}"
export XBT_MYSQL_PASSWORD="${XBT_MYSQL_PASSWORD:-tracker-pass}"
export XBT_LISTEN_HTTP_PORT="${XBT_LISTEN_HTTP_PORT:-2710}"
export XBT_LISTEN_UDP_PORT="${XBT_LISTEN_UDP_PORT:-6881}"
export XBT_AUTO_REGISTER="${XBT_AUTO_REGISTER:-0}"
export XBT_ANONYMOUS_ANNOUNCE="${XBT_ANONYMOUS_ANNOUNCE:-0}"
export XBT_ANONYMOUS_SCRAPE="${XBT_ANONYMOUS_SCRAPE:-0}"
export XBT_FULL_SCRAPE="${XBT_FULL_SCRAPE:-0}"

mkdir -p /etc/xbt
envsubst < /etc/xbt/xbt_tracker.conf.template > /etc/xbt/xbt_tracker.conf

until nc -z "$XBT_MYSQL_HOST" "$XBT_MYSQL_PORT"; do
  echo "waiting for tracker database at ${XBT_MYSQL_HOST}:${XBT_MYSQL_PORT}"
  sleep 2
done

exec /src/xbt/Tracker/build/xbt_tracker /etc/xbt/xbt_tracker.conf
