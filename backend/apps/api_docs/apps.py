from django.apps import AppConfig


class ApiDocsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_docs"
    verbose_name = "API 文档"

    def ready(self):
        from apps.api_docs import openapi  # noqa: F401
