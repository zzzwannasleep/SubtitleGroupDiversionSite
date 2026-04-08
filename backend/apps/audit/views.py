from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.common.permissions import IsAdminRole
from apps.common.responses import success_response


class AuditLogListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        logs = AuditLog.objects.all()[:100]
        return success_response(AuditLogSerializer(logs, many=True).data)
