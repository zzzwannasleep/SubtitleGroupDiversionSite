import logging
import os
from pathlib import Path


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


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = env("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    item.strip() for item in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if item.strip()
]

SITE_BASE_URL = env("SITE_BASE_URL", "http://localhost:8000").rstrip("/")
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
    "DESCRIPTION": "内部字幕组分流站点后端 API。",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api",
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
