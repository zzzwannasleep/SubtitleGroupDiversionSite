from django.urls import path

from apps.tracker_sync.views import (
    TrackerSyncFullView,
    TrackerSyncLogListView,
    TrackerSyncLogRetryView,
    TrackerSyncOverviewView,
    TrackerSyncReleaseView,
)


urlpatterns = [
    path("admin/tracker-sync/overview/", TrackerSyncOverviewView.as_view(), name="tracker-sync-overview"),
    path("admin/tracker-sync/logs/", TrackerSyncLogListView.as_view(), name="tracker-sync-logs"),
    path("admin/tracker-sync/logs/<int:log_id>/retry/", TrackerSyncLogRetryView.as_view(), name="tracker-sync-log-retry"),
    path("admin/tracker-sync/full/", TrackerSyncFullView.as_view(), name="tracker-sync-full"),
    path(
        "admin/tracker-sync/releases/<int:release_id>/",
        TrackerSyncReleaseView.as_view(),
        name="tracker-sync-release",
    ),
]
