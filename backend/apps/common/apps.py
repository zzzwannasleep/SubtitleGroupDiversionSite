import logging

from django.conf import settings
from django.apps import AppConfig


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
            "backend startup configuration loaded debug=%s site_base_url=%s xbt_sync_enabled=%s",
            settings.DEBUG,
            settings.SITE_BASE_URL,
            settings.XBT_SYNC_ENABLED,
        )
        CommonConfig._startup_logged = True
