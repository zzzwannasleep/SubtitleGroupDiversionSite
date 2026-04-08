from django.urls import path

from apps.tracker_sync.views import TrackerSyncFullView, TrackerSyncLogListView, TrackerSyncReleaseView


urlpatterns = [
    path("admin/tracker-sync/logs/", TrackerSyncLogListView.as_view(), name="tracker-sync-logs"),
    path("admin/tracker-sync/full/", TrackerSyncFullView.as_view(), name="tracker-sync-full"),
    path(
        "admin/tracker-sync/releases/<int:release_id>/",
        TrackerSyncReleaseView.as_view(),
        name="tracker-sync-release",
    ),
]
