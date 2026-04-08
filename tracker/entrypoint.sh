#!/bin/sh
set -eu

CONFIG_FILE="${XBT_CONFIG_FILE:-/etc/xbt/xbt_tracker.conf}"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Missing tracker config: $CONFIG_FILE" >&2
  exit 1
fi

exec /usr/local/bin/xbt_tracker "$CONFIG_FILE"
