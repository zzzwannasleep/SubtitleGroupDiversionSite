import logging

from django.apps import AppConfig
from django.conf import settings


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "公共组件"
    _startup_logged = False

    def ready(self):
        if CommonConfig._startup_logged:
            return

        logger = logging.getLogger("apps.startup")
        logger.info(
            "backend startup configuration loaded debug=%s site_base_url=%s",
            settings.DEBUG,
            settings.SITE_BASE_URL,
        )
        CommonConfig._startup_logged = True
