from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.common.permissions import IsAdminRole
from apps.common.responses import success_response
from apps.releases.models import Release
from apps.tracker_sync.models import TrackerSyncLog
from apps.tracker_sync.serializers import TrackerSyncLogSerializer
from apps.tracker_sync.services import TrackerSyncService


class TrackerSyncLogListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        logs = TrackerSyncLog.objects.all()[:100]
        return success_response(TrackerSyncLogSerializer(logs, many=True).data)


class TrackerSyncFullView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        log = TrackerSyncService.sync_all()
        AuditService.log(
            request.user,
            "手动触发全量 XBT 同步",
            "XBT",
            "全量同步",
            detail=f"同步结果：{log.status}",
            payload={"tracker_sync_log_id": log.id},
        )
        return success_response(TrackerSyncLogSerializer(log).data, message="已触发全量同步。")


class TrackerSyncReleaseView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, release_id: int):
        release = get_object_or_404(Release, pk=release_id)
        log = TrackerSyncService.sync_release(release)
        AuditService.log(
            request.user,
            "手动同步资源到 XBT",
            "资源",
            release.title,
            detail=f"同步结果：{log.status}",
            payload={"release_id": release.id, "tracker_sync_log_id": log.id},
        )
        return success_response(TrackerSyncLogSerializer(log).data)
