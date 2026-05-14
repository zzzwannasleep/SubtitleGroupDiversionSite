#!/bin/sh
set -eu

is_truthy() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

warn() {
  echo "Warning: $*" >&2
}

ensure_compose_profile() {
  profile="$1"
  case ",${COMPOSE_PROFILES:-}," in
    *,"$profile",*) ;;
    ",,") COMPOSE_PROFILES="$profile" ;;
    *) COMPOSE_PROFILES="${COMPOSE_PROFILES},$profile" ;;
  esac
  export COMPOSE_PROFILES
}

looks_like_tracker_proxy_url() {
  case "${1:-}" in
    */tracker/announce*|*/tracker/scrape*|*/tracker/*/announce*|*/tracker/*/scrape*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

validate_tracker_configuration() {
  if ! is_truthy "${TRACKER_ENABLED:-false}"; then
    return 0
  fi

  if [ -z "${TRACKER_ANNOUNCE_URL:-}" ]; then
    warn "TRACKER_ENABLED=true but TRACKER_ANNOUNCE_URL is empty."
  fi

  if [ -z "${TORRUST_API_URL:-}" ]; then
    warn "TRACKER_ENABLED=true but TORRUST_API_URL is empty."
  fi

  if [ -z "${TORRUST_API_TOKEN:-}" ]; then
    warn "TRACKER_ENABLED=true but TORRUST_API_TOKEN is empty."
  fi

  proxy_mode=false
  if looks_like_tracker_proxy_url "${TRACKER_ANNOUNCE_URL:-}" || looks_like_tracker_proxy_url "${TRACKER_PUBLIC_SCRAPE_URL:-}"; then
    proxy_mode=true
  fi

  if [ "$proxy_mode" = "true" ] && [ -z "${TRACKER_INTERNAL_ANNOUNCE_URL:-}" ]; then
    warn "TRACKER_ANNOUNCE_URL points to the Django /tracker proxy, but TRACKER_INTERNAL_ANNOUNCE_URL is empty. Set it to the internal Torrust announce URL, for example http://tracker:7070/announce."
  fi

  if [ "$proxy_mode" = "true" ] && [ -f ./tracker/tracker.toml ]; then
    if ! grep -Eq '^[[:space:]]*on_reverse_proxy[[:space:]]*=[[:space:]]*true([[:space:]]*#.*)?$' ./tracker/tracker.toml; then
      warn "Proxy mode is enabled, but deploy/tracker/tracker.toml still does not contain 'on_reverse_proxy = true' under [core.net]."
    fi
  fi
}

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

bootstrap_tracker=false
if is_truthy "${TRACKER_ENABLED:-false}"; then
  bootstrap_tracker=true
  ensure_compose_profile "tracker"
  if [ ! -f ./tracker/tracker.toml ]; then
    cp ./tracker/tracker.example.toml ./tracker/tracker.toml
    echo "Created deploy/tracker/tracker.toml from the example file. Review it if you need custom tracker settings."
  fi
fi

validate_tracker_configuration

if [ "${IMAGE_PULL_POLICY:-always}" != "never" ]; then
  docker compose pull
fi

if [ "$bootstrap_tracker" = "true" ]; then
  docker compose up -d mysql redis tracker
else
  docker compose up -d mysql redis
fi

echo "Waiting for MySQL to become ready..."
until docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent >/dev/null 2>&1; do
  sleep 2
done

docker compose up -d backend

echo "Waiting for backend to become ready..."
backend_wait_timeout="${BACKEND_STARTUP_TIMEOUT_SECONDS:-180}"
backend_wait_started_at="$(date +%s)"
until docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=3).read()" >/dev/null 2>&1; do
  backend_wait_now="$(date +%s)"
  if [ $((backend_wait_now - backend_wait_started_at)) -ge "$backend_wait_timeout" ]; then
    echo "Backend did not become ready within ${backend_wait_timeout}s. Check 'docker compose logs backend' for details." >&2
    exit 1
  fi
  sleep 2
done

echo "Run 'cd deploy && docker compose exec backend python manage.py createsuperuser' to create the first admin user."
