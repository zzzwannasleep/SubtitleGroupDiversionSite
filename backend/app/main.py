import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware

from app.api import admin, auth, categories, health, rss, site_settings, torrents, users
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.internal_admin import configure_internal_admin, sync_internal_admin_title
from app.models import import_all_models
from app.services.bootstrap_service import seed_default_categories


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
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(torrents.router)
app.include_router(rss.router)
app.include_router(site_settings.router)
app.include_router(admin.router)
configure_internal_admin(app)
