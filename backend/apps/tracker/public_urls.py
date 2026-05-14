from django.urls import path

from apps.tracker.proxy_views import TrackerAnnounceProxyView, TrackerScrapeProxyView


urlpatterns = [
    path("announce/<str:auth_key>", TrackerAnnounceProxyView.as_view(), name="tracker-announce-suffix"),
    path("<str:auth_key>/announce", TrackerAnnounceProxyView.as_view(), name="tracker-announce-prefix"),
    path("scrape/<str:auth_key>", TrackerScrapeProxyView.as_view(), name="tracker-scrape-suffix"),
    path("<str:auth_key>/scrape", TrackerScrapeProxyView.as_view(), name="tracker-scrape-prefix"),
]
