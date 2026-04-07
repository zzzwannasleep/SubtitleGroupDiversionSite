import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware

from app.api import admin, auth, categories, health, rss, site_settings, torrents, users
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.errors import REQUEST_ID_HEADER, configure_error_handlers
from app.internal_admin import configure_internal_admin, sync_internal_admin_title
from app.models import import_all_models
from app.services.bootstrap_service import seed_default_categories
from app.services.tracker_sync_service import sync_tracker_stats


settings = get_settings()
logger = logging.getLogger(__name__)


async def wait_for_database(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            if attempt > 1:
                logger.info("Database became available on startup attempt %s", attempt)
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Database not ready on startup attempt %s/%s: %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                await asyncio.sleep(delay_seconds)

    raise RuntimeError(f"Database did not become ready after {max_attempts} attempts") from last_error


def run_tracker_sync_once() -> None:
    with SessionLocal() as db:
        result = sync_tracker_stats(db)
        if result.get("skipped"):
            logger.info("Scheduled tracker sync skipped: %s", result.get("message"))
            return
        logger.info(
            "Scheduled tracker sync completed: %s user stats, %s torrent stats",
            result.get("user_stats_updated", 0),
            result.get("torrent_stats_updated", 0),
        )


def should_start_tracker_sync_scheduler() -> bool:
    if settings.tracker_sync_interval_seconds <= 0:
        return False

    sync_mode = settings.tracker_sync_mode.strip().lower()
    if sync_mode == "xbt_db":
        if settings.tracker_impl.strip().lower() == "xbt" and settings.xbt_tracker_db_dsn:
            return True
        logger.info("Scheduled tracker sync disabled because XBT database sync is not configured")
        return False

    if sync_mode == "pull":
        if settings.tracker_user_stats_endpoint or settings.tracker_torrent_stats_endpoint:
            return True
        logger.info("Scheduled tracker sync disabled because tracker sync endpoints are not configured")
        return False

    logger.info("Scheduled tracker sync disabled for unsupported mode '%s'", settings.tracker_sync_mode)
    return False


async def run_tracker_sync_loop(interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(run_tracker_sync_once)
        except Exception as exc:
            logger.warning("Scheduled tracker sync failed: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    import_all_models()
    await wait_for_database()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    sync_internal_admin_title()

    if inspect(engine).has_table("categories"):
        with SessionLocal() as db:
            seed_default_categories(db)

    tracker_sync_task: asyncio.Task[None] | None = None
    if should_start_tracker_sync_scheduler():
        tracker_sync_task = asyncio.create_task(run_tracker_sync_loop(settings.tracker_sync_interval_seconds))
        logger.info("Scheduled tracker sync enabled every %s seconds", settings.tracker_sync_interval_seconds)

    try:
        yield
    finally:
        if tracker_sync_task is not None:
            tracker_sync_task.cancel()
            with suppress(asyncio.CancelledError):
                await tracker_sync_task


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")
configure_error_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(torrents.router)
app.include_router(rss.router)
app.include_router(site_settings.router)
app.include_router(admin.router)
configure_internal_admin(app)
