#!/bin/sh
set -eu

uvicorn_log_level=$(printf '%s' "${APP_LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
if [ "$uvicorn_log_level" = "warn" ]; then
  uvicorn_log_level=warning
fi

case "$uvicorn_log_level" in
  critical|error|warning|info|debug|trace)
    ;;
  *)
    echo "[warning] backend-entrypoint: unsupported APP_LOG_LEVEL='${APP_LOG_LEVEL:-}', falling back to info" >&2
    uvicorn_log_level=info
    ;;
esac

echo "[info] backend-entrypoint: starting uvicorn with log level ${uvicorn_log_level}"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level "$uvicorn_log_level" --access-log
