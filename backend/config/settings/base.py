import logging
import os
from pathlib import Path
from urllib.parse import urlsplit


BASE_DIR = Path(__file__).resolve().parents[2]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or name in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[name] = value


load_env_file(BASE_DIR / ".env")


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_host(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()
    if not candidate:
        return None
    if candidate == "*":
        return candidate

    parsed = urlsplit(candidate if "://" in candidate else f"//{candidate}")
    return parsed.hostname or candidate


def build_allowed_hosts(raw_hosts: str | None, site_base_url: str) -> list[str]:
    hosts: list[str] = []
    for item in split_csv(raw_hosts):
        host = normalize_host(item)
        if host and host not in hosts:
            hosts.append(host)

    site_host = normalize_host(site_base_url)
    if site_host and site_host not in hosts:
        hosts.append(site_host)

    return hosts or ["*"]


def build_csrf_trusted_origins(raw_origins: str | None, site_base_url: str) -> list[str]:
    origins = split_csv(raw_origins)
    parsed = urlsplit(site_base_url)
    if parsed.scheme and parsed.netloc:
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in origins:
            origins.append(origin)
    return origins


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = env("DJANGO_DEBUG", "false").lower() == "true"
SITE_BASE_URL = env("SITE_BASE_URL", "http://localhost:8000").rstrip("/")
ALLOWED_HOSTS = build_allowed_hosts(env("DJANGO_ALLOWED_HOSTS"), SITE_BASE_URL)
CSRF_TRUSTED_ORIGINS = build_csrf_trusted_origins(env("DJANGO_CSRF_TRUSTED_ORIGINS"), SITE_BASE_URL)
LOG_LEVEL = env("LOG_LEVEL", "INFO")
REDIS_URL = env("REDIS_URL")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.api_docs",
    "apps.common",
    "apps.authx",
    "apps.users",
    "apps.releases",
    "apps.downloads",
    "apps.rss",
    "apps.announcements",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.common.middleware.RequestLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if env("MYSQL_DATABASE"):
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("MYSQL_DATABASE"),
        "USER": env("MYSQL_USER", "subtitle"),
        "PASSWORD": env("MYSQL_PASSWORD", ""),
        "HOST": env("MYSQL_HOST", "localhost"),
        "PORT": env("MYSQL_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Shanghai")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
FRONTEND_DIST_DIR = BASE_DIR / "frontend_dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "subtitle-group-diversion-site",
    }
}

if REDIS_URL:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.common.authentication.UserApiTokenAuthentication",
        "apps.common.authentication.UserApiKeyAuthentication",
        "apps.common.authentication.CsrfExemptSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/minute",
        "rss": "120/hour",
        "download": "240/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Subtitle Group Diversion Site API",
    "DESCRIPTION": (
        "内部字幕组分流站点后端 API。\n\n"
        "推荐阅读顺序：先看 `Auth` 完成登录，再按 `Site`、`Releases`、`Downloads`、`RSS`、`Profile` 使用前台能力；"
        "后台接口统一放在 `Admin ...` 分组下。\n\n"
        "认证方式：\n"
        "- 浏览器调试优先使用 Session / Cookie 登录。\n"
        "- 脚本调用可使用 `Authorization: Token <api_token>`、`Authorization: Bearer <api_token>`，"
        "或 `X-API-Key: <api_token>`。\n"
        "- 文件上传接口请使用 `multipart/form-data`。"
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api",
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Auth", "description": "登录、注册、退出登录、获取当前用户与修改密码。"},
        {"name": "Site", "description": "前台公开或当前用户可见的站点信息，例如公告与站点设置。"},
        {"name": "Releases", "description": "前台资源浏览、详情、创建、编辑，以及“我的发布”。"},
        {"name": "Downloads", "description": "torrent 下载与当前用户下载记录。"},
        {"name": "RSS", "description": "RSS 概览与按站点、分类、标签输出的订阅源。"},
        {"name": "Profile", "description": "当前登录用户的个性化设置与 API Token 自助管理。"},
        {"name": "Admin Dashboard", "description": "后台仪表盘概览数据。"},
        {"name": "Admin Users", "description": "后台用户管理与用户状态调整。"},
        {"name": "Admin Invite Codes", "description": "邀请码查询、批量生成与停用。"},
        {"name": "Admin Releases", "description": "后台资源列表与可见状态控制。"},
        {"name": "Admin Taxonomy", "description": "后台分类与标签维护。"},
        {"name": "Admin Site", "description": "后台公告与站点设置管理。"},
        {"name": "Admin Audit", "description": "后台审计日志查询。"},
    ],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
    },
    "ENUM_NAME_OVERRIDES": {
        "UserRoleEnum": [("admin", "管理员"), ("uploader", "上传者"), ("user", "普通用户")],
        "UserStatusEnum": [("active", "正常"), ("disabled", "禁用")],
        "ReleaseStatusEnum": [("draft", "草稿"), ("published", "已发布"), ("hidden", "已隐藏")],
        "AnnouncementStatusEnum": [("online", "上线"), ("draft", "草稿"), ("offline", "下线")],
        "AnnouncementAudienceEnum": [("all", "全部"), ("uploader", "上传者"), ("admin", "管理员")],
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "apps.request": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

logging.captureWarnings(True)
