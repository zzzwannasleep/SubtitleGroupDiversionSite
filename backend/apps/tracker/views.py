from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.views import APIView

from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.tracker.serializers import (
    AdminTrackerOverviewSerializer,
    AdminTrackerSyncRequestSerializer,
    AdminTrackerSyncResultSerializer,
    SelfTrackerProfileSerializer,
)
from apps.tracker.services import TrackerAdminService, TrackerService


@extend_schema_view(
    get=extend_schema(
        operation_id="users_tracker_profile",
        summary="获取当前用户的 Private Tracker 信息",
        tags=["Profile"],
        responses=success_response_schema("SelfTrackerProfileResponse", SelfTrackerProfileSerializer),
    ),
)
class SelfTrackerProfileView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        if not TrackerService.is_enabled():
            data = {
                "enabled": False,
                "authMode": TrackerService.auth_mode(),
                "announceUrl": "",
                "scrapeUrl": "",
                "passkey": "",
                "keyValidUntil": None,
                "requireAuthDownloads": False,
                "forcePrivateTorrents": False,
            }
            return success_response(data)

        passkey = ""
        key_valid_until = None
        if TrackerService.auth_mode() == "per_user":
            passkey = TrackerService.ensure_user_key(request.user)
            key_valid_until = request.user.tracker_key_valid_until

        return success_response(
            {
                "enabled": True,
                "authMode": TrackerService.auth_mode(),
                "announceUrl": TrackerService.get_announce_url_for_user(request.user),
                "scrapeUrl": TrackerService.get_scrape_url_for_user(request.user),
                "passkey": passkey,
                "keyValidUntil": key_valid_until,
                "requireAuthDownloads": TrackerService.require_authenticated_downloads(),
                "forcePrivateTorrents": TrackerService.force_private_torrents(),
            }
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_tracker_overview",
        summary="获取 Private Tracker 概览",
        tags=["Admin Tracker"],
        responses=success_response_schema("AdminTrackerOverviewResponse", AdminTrackerOverviewSerializer),
    ),
)
class AdminTrackerOverviewView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(TrackerAdminService.get_overview())


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_tracker_sync",
        summary="手动同步 Private Tracker 状态",
        tags=["Admin Tracker"],
        request=AdminTrackerSyncRequestSerializer,
        responses=success_response_schema("AdminTrackerSyncResponse", AdminTrackerSyncResultSerializer),
    ),
)
class AdminTrackerSyncView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = AdminTrackerSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = TrackerAdminService.sync(
            sync_users=serializer.validated_data.get("syncUsers", False),
            sync_releases=serializer.validated_data.get("syncReleases", False),
            sync_scrape=serializer.validated_data.get("syncScrape", False),
        )
        return success_response(data, message="Tracker 同步已完成。")
