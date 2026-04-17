from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.common.throttles import TorrentDownloadThrottle
from apps.downloads.models import DownloadLog
from apps.downloads.serializers import DownloadLogSerializer
from apps.downloads.services import DownloadService
from apps.releases.models import Release


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_download_torrent",
        summary="下载 torrent",
        tags=["Downloads"],
        parameters=[
            OpenApiParameter(name="passkey", description="未登录时可通过 passkey 下载 torrent。", type=str),
        ],
        responses={
            (200, "application/x-bittorrent"): OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="torrent 文件。",
            )
        },
    ),
)
class ReleaseDownloadView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [TorrentDownloadThrottle]

    def get(self, request, release_id: int):
        release = get_object_or_404(Release.objects.select_related("created_by"), pk=release_id)
        user = DownloadService.resolve_user(request)
        torrent_bytes, filename = DownloadService.build_download_torrent(user=user, release=release, request=request)
        response = HttpResponse(torrent_bytes, content_type="application/x-bittorrent")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@extend_schema_view(
    get=extend_schema(
        operation_id="users_download_logs",
        summary="获取当前用户下载记录",
        tags=["Downloads"],
        responses=success_response_schema("DownloadLogListResponse", DownloadLogSerializer(many=True)),
    ),
)
class MyDownloadListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        logs = DownloadLog.objects.select_related("release", "user").filter(user=request.user)
        return success_response(DownloadLogSerializer(logs, many=True).data)
