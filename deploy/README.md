# Deploy

1. Copy `deploy/.env.example` to `deploy/.env`.
2. Fill in the small set of required variables.
3. Run `sh deploy/scripts/init.sh`.
4. Create the first admin user with `docker compose -f deploy/docker-compose.yml exec backend python manage.py createsuperuser`.

Notes:

- `deploy/scripts/render-xbt-config.sh` renders `deploy/xbt/xbt_tracker.conf` from `deploy/.env` so XBT credentials do not need to live in versioned files.
- `deploy/scripts/init.sh` also imports the bundled `xbt_tracker.sql` schema into MySQL on first boot.
- `deploy/docker-compose.yml` is production-oriented and prefers `image:` over `build:`.
- `backend` and `nginx` share volumes for `/media` and `/static`, so Django uploads and collected static files survive container replacement.
