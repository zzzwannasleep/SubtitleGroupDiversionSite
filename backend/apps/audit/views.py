from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.common.permissions import IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import success_response_schema


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_audit_logs_list",
        summary="获取审计日志",
        tags=["Audit"],
        parameters=[
            OpenApiParameter(name="q", description="关键词，支持操作人、动作、对象类型、对象名称和详情。", type=str),
            OpenApiParameter(name="targetType", description="按对象类型筛选。", type=str),
            OpenApiParameter(name="limit", description="返回条数，默认 100，最大 200。", type=int),
        ],
        responses=success_response_schema("AuditLogListResponse", AuditLogSerializer(many=True)),
    ),
)
class AuditLogListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        keyword = (request.query_params.get("q") or "").strip()
        target_type = (request.query_params.get("targetType") or "").strip()
        try:
            limit = min(max(int(request.query_params.get("limit", 100)), 1), 200)
        except (TypeError, ValueError):
            limit = 100

        logs = AuditLog.objects.all()
        if keyword:
            logs = logs.filter(
                Q(actor_name__icontains=keyword)
                | Q(action__icontains=keyword)
                | Q(target_type__icontains=keyword)
                | Q(target_name__icontains=keyword)
                | Q(detail__icontains=keyword)
            )
        if target_type:
            logs = logs.filter(target_type=target_type)

        return success_response(AuditLogSerializer(logs[:limit], many=True).data)
