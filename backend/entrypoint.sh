#!/bin/sh
set -eu

is_truthy() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

tracker_startup_sync() {
  if ! is_truthy "${TRACKER_ENABLED:-false}"; then
    return 0
  fi

  if [ -n "${TRACKER_AUTO_SYNC_ON_START:-}" ] && ! is_truthy "${TRACKER_AUTO_SYNC_ON_START}"; then
    echo "Skipping tracker startup sync because TRACKER_AUTO_SYNC_ON_START is disabled."
    return 0
  fi

  timeout_seconds="${TRACKER_AUTO_SYNC_TIMEOUT_SECONDS:-90}"
  retry_interval_seconds="${TRACKER_AUTO_SYNC_RETRY_INTERVAL_SECONDS:-5}"
  sync_args="--users --releases"
  start_time="$(date +%s)"

  if is_truthy "${TRACKER_AUTO_SYNC_INCLUDE_SCRAPE:-false}"; then
    sync_args="$sync_args --scrape"
  fi

  echo "Tracker is enabled. Waiting for Torrust API before running startup sync..."

  while ! python manage.py shell -c "from apps.tracker.services import TorrustClient; TorrustClient.from_settings().get_stats()" >/dev/null 2>&1; do
    current_time="$(date +%s)"
    elapsed_seconds=$((current_time - start_time))
    if [ "$elapsed_seconds" -ge "$timeout_seconds" ]; then
      echo "Tracker API was not reachable within ${timeout_seconds}s." >&2
      if is_truthy "${TRACKER_SYNC_STRICT:-false}"; then
        return 1
      fi
      echo "Continuing startup without tracker bootstrap because TRACKER_SYNC_STRICT is disabled." >&2
      return 0
    fi

    echo "Tracker API is not ready yet. Retrying in ${retry_interval_seconds}s..."
    sleep "$retry_interval_seconds"
  done

  echo "Tracker API is ready. Running startup tracker sync..."
  python manage.py sync_tracker_state $sync_args
}

python manage.py migrate --noinput
python manage.py collectstatic --noinput
tracker_startup_sync

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --access-logfile - \
  --error-logfile -
