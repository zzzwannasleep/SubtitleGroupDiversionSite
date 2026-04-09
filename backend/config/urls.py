from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("system-admin/", admin.site.urls),
    path("api/", include("apps.authx.urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.releases.urls")),
    path("api/", include("apps.downloads.urls")),
    path("api/", include("apps.announcements.urls")),
    path("api/", include("apps.audit.urls")),
    path("api/", include("apps.tracker_sync.urls")),
    path("api/", include("apps.rss.api_urls")),
    path("rss/", include("apps.rss.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
