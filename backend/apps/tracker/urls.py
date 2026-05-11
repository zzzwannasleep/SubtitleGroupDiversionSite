from django.urls import path

from apps.tracker.views import (
    AdminTrackerOverviewView,
    AdminTrackerSyncView,
    SelfTrackerProfileView,
)


urlpatterns = [
    path("me/tracker/", SelfTrackerProfileView.as_view(), name="me-tracker"),
    path("admin/tracker/overview/", AdminTrackerOverviewView.as_view(), name="admin-tracker-overview"),
    path("admin/tracker/sync/", AdminTrackerSyncView.as_view(), name="admin-tracker-sync"),
]
