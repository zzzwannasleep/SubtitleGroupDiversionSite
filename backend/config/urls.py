from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, HttpResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as static_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


def serve_frontend_index(_request):
    index_path = settings.FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        return HttpResponse(
            "Frontend build is not available. Start the Vite dev server or rebuild the backend image.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    return FileResponse(index_path.open("rb"), content_type="text/html")


urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("system-admin/", admin.site.urls),
    path("api/", include("apps.authx.urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.releases.urls")),
    path("api/", include("apps.downloads.urls")),
    path("api/", include("apps.announcements.urls")),
    path("api/", include("apps.audit.urls")),
    path("api/", include("apps.rss.api_urls")),
    path("rss/", include("apps.rss.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc-ui"),
    re_path(r"^static/(?P<path>.*)$", static_serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", static_serve, {"document_root": settings.MEDIA_ROOT}),
]

if settings.FRONTEND_ASSETS_DIR.exists():
    urlpatterns += [
        re_path(r"^assets/(?P<path>.*)$", static_serve, {"document_root": settings.FRONTEND_ASSETS_DIR}),
        re_path(
            r"^(?!api/|rss/|media/|static/|assets/|system-admin/|health/)(?!.*\.[^/]+$).*$",
            serve_frontend_index,
            name="spa-index",
        ),
    ]
