from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actorName = serializers.CharField(source="actor_name")
    targetType = serializers.CharField(source="target_type")
    targetName = serializers.CharField(source="target_name")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = AuditLog
        fields = ("id", "actorName", "action", "targetType", "targetName", "createdAt", "detail")
