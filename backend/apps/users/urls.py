from django.urls import path

from apps.users.views import (
    AdminDashboardView,
    AdminInviteCodeListCreateView,
    AdminInviteCodeRevokeView,
    AdminTrackerSyncUserView,
    AdminUserDetailView,
    AdminUserDisableView,
    AdminUserEnableView,
    AdminUserListCreateView,
    AdminUserResetPasskeyView,
    AdminUserStatusView,
    SelfApiTokenView,
    SelfPasskeyResetView,
    SelfThemeView,
)


urlpatterns = [
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/invite-codes/", AdminInviteCodeListCreateView.as_view(), name="admin-invite-codes"),
    path(
        "admin/invite-codes/<int:invite_code_id>/revoke/",
        AdminInviteCodeRevokeView.as_view(),
        name="admin-invite-code-revoke",
    ),
    path("admin/users/", AdminUserListCreateView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/users/<int:user_id>/status/", AdminUserStatusView.as_view(), name="admin-user-status"),
    path("admin/users/<int:user_id>/disable/", AdminUserDisableView.as_view(), name="admin-user-disable"),
    path("admin/users/<int:user_id>/enable/", AdminUserEnableView.as_view(), name="admin-user-enable"),
    path(
        "admin/users/<int:user_id>/reset-passkey/",
        AdminUserResetPasskeyView.as_view(),
        name="admin-user-reset-passkey",
    ),
    path("admin/tracker-sync/users/<int:user_id>/", AdminTrackerSyncUserView.as_view(), name="admin-tracker-sync-user"),
    path("me/reset-passkey/", SelfPasskeyResetView.as_view(), name="me-reset-passkey"),
    path("me/api-token/", SelfApiTokenView.as_view(), name="me-api-token"),
    path("me/theme/", SelfThemeView.as_view(), name="me-theme"),
]
