from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.common.permissions import IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.releases.models import Release
from apps.tracker_sync.models import TrackerSyncLog, TrackerSyncScope, TrackerSyncStatus
from apps.tracker_sync.serializers import (
    TrackerSyncLogSerializer,
    TrackerSyncOverviewSerializer,
    TrackerSyncReleaseDetailSerializer,
)
from apps.tracker_sync.services import TrackerSyncService


@extend_schema_view(
    get=extend_schema(
        operation_id="tracker_sync_overview",
        summary="获取 XBT 同步概览",
        tags=["Tracker Sync"],
        responses=success_response_schema("TrackerSyncOverviewResponse", TrackerSyncOverviewSerializer),
    ),
)
class TrackerSyncOverviewView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        serializer = TrackerSyncOverviewSerializer(TrackerSyncService.build_overview())
        return success_response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        operation_id="tracker_sync_logs_list",
        summary="获取 XBT 同步日志",
        tags=["Tracker Sync"],
        parameters=[
            OpenApiParameter(name="scope", description="同步范围筛选。", enum=TrackerSyncScope.values),
            OpenApiParameter(name="status", description="同步状态筛选。", enum=TrackerSyncStatus.values),
            OpenApiParameter(name="userId", description="按用户 ID 筛选。", type=int),
            OpenApiParameter(name="releaseId", description="按资源 ID 筛选。", type=int),
            OpenApiParameter(name="q", description="按目标名称或说明搜索。", type=str),
            OpenApiParameter(name="limit", description="返回条数，默认 100，最大 200。", type=int),
        ],
        responses=success_response_schema("TrackerSyncLogListResponse", TrackerSyncLogSerializer(many=True)),
    ),
)
class TrackerSyncLogListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        scope = (request.query_params.get("scope") or "").strip()
        status = (request.query_params.get("status") or "").strip()
        keyword = (request.query_params.get("q") or "").strip()
        try:
            user_id = int(request.query_params["userId"]) if request.query_params.get("userId") else None
        except (TypeError, ValueError):
            user_id = None
        try:
            release_id = int(request.query_params["releaseId"]) if request.query_params.get("releaseId") else None
        except (TypeError, ValueError):
            release_id = None
        try:
            limit = min(max(int(request.query_params.get("limit", 100)), 1), 200)
        except (TypeError, ValueError):
            limit = 100

        logs = TrackerSyncLog.objects.all()
        if scope in TrackerSyncScope.values:
            logs = logs.filter(scope=scope)
        if status in TrackerSyncStatus.values:
            logs = logs.filter(status=status)
        if user_id is not None:
            logs = logs.filter(user_id=user_id)
        if release_id is not None:
            logs = logs.filter(release_id=release_id)
        if keyword:
            logs = logs.filter(Q(target_name__icontains=keyword) | Q(message__icontains=keyword))
        return success_response(TrackerSyncLogSerializer(logs[:limit], many=True).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="tracker_sync_full_run",
        summary="执行全量 XBT 同步",
        tags=["Tracker Sync"],
        request=None,
        responses=success_response_schema("TrackerSyncFullResponse", TrackerSyncLogSerializer),
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        operation_id="tracker_sync_release_detail",
        summary="获取指定资源的 XBT 同步详情",
        tags=["Tracker Sync"],
        responses=success_response_schema("TrackerSyncReleaseDetailResponse", TrackerSyncReleaseDetailSerializer),
    ),
    post=extend_schema(
        operation_id="tracker_sync_release_run",
        summary="同步指定资源到 XBT",
        tags=["Tracker Sync"],
        request=None,
        responses=success_response_schema("TrackerSyncReleaseResponse", TrackerSyncLogSerializer),
    ),
)
class TrackerSyncReleaseView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, release_id: int):
        release = get_object_or_404(Release, pk=release_id)
        serializer = TrackerSyncReleaseDetailSerializer(TrackerSyncService.build_release_detail(release))
        return success_response(serializer.data)

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


@extend_schema_view(
    post=extend_schema(
        operation_id="tracker_sync_log_retry",
        summary="按同步日志重试 XBT 同步",
        tags=["Tracker Sync"],
        request=None,
        responses=success_response_schema("TrackerSyncLogRetryResponse", TrackerSyncLogSerializer),
    ),
)
class TrackerSyncLogRetryView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, log_id: int):
        source_log = get_object_or_404(TrackerSyncLog, pk=log_id)
        log = TrackerSyncService.retry_log(source_log)
        AuditService.log(
            request.user,
            "手动重试 XBT 同步",
            "XBT",
            source_log.target_name,
            detail=f"源日志 #{source_log.id}，重试结果：{log.status}",
            payload={"source_tracker_sync_log_id": source_log.id, "tracker_sync_log_id": log.id},
        )
        return success_response(TrackerSyncLogSerializer(log).data, message="已触发同步重试。")
