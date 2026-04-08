from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.downloads.models import DownloadLog
from apps.downloads.serializers import DownloadLogSerializer
from apps.downloads.services import DownloadService
from apps.releases.models import Release


class ReleaseDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, release_id: int):
        release = get_object_or_404(Release.objects.select_related("created_by"), pk=release_id)
        user = DownloadService.resolve_user(request)
        torrent_bytes, filename = DownloadService.build_personalized_torrent(
            user=user, release=release, request=request
        )
        response = HttpResponse(torrent_bytes, content_type="application/x-bittorrent")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class MyDownloadListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        logs = DownloadLog.objects.select_related("release", "user").filter(user=request.user)
        return success_response(DownloadLogSerializer(logs, many=True).data)
