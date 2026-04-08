from rest_framework import serializers

from apps.tracker_sync.models import TrackerSyncLog


class TrackerSyncLogSerializer(serializers.ModelSerializer):
    targetName = serializers.CharField(source="target_name")
    updatedAt = serializers.DateTimeField(source="updated_at")

    class Meta:
        model = TrackerSyncLog
        fields = ("id", "scope", "targetName", "status", "message", "updatedAt")
