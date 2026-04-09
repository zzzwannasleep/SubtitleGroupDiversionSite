from django.urls import path

from apps.users.views import (
    AdminDashboardView,
    AdminTrackerSyncUserView,
    AdminUserDetailView,
    AdminUserListCreateView,
    AdminUserResetPasskeyView,
    AdminUserStatusView,
    SelfPasskeyResetView,
    SelfThemeView,
)


urlpatterns = [
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/users/", AdminUserListCreateView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/users/<int:user_id>/status/", AdminUserStatusView.as_view(), name="admin-user-status"),
    path(
        "admin/users/<int:user_id>/reset-passkey/",
        AdminUserResetPasskeyView.as_view(),
        name="admin-user-reset-passkey",
    ),
    path("admin/tracker-sync/users/<int:user_id>/", AdminTrackerSyncUserView.as_view(), name="admin-tracker-sync-user"),
    path("me/reset-passkey/", SelfPasskeyResetView.as_view(), name="me-reset-passkey"),
    path("me/theme/", SelfThemeView.as_view(), name="me-theme"),
]
