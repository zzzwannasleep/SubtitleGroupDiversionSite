from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from starlette.middleware.sessions import SessionMiddleware

from app.api import admin, auth, categories, health, rss, site_settings, torrents, users
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.internal_admin import configure_internal_admin, sync_internal_admin_title
from app.models import import_all_models
from app.services.bootstrap_service import seed_default_categories


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    import_all_models()
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
