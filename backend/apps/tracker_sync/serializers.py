from rest_framework import serializers

from apps.tracker_sync.models import TrackerSyncLog


class TrackerSyncSnapshotSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    updatedAt = serializers.DateTimeField()


class XbtUserSnapshotSerializer(serializers.Serializer):
    state = serializers.CharField()
    canLeech = serializers.BooleanField(allow_null=True)
    downloaded = serializers.IntegerField(allow_null=True)
    uploaded = serializers.IntegerField(allow_null=True)
    completed = serializers.IntegerField(allow_null=True)


class XbtFileSnapshotSerializer(serializers.Serializer):
    state = serializers.CharField()
    seeders = serializers.IntegerField(allow_null=True)
    leechers = serializers.IntegerField(allow_null=True)
    completed = serializers.IntegerField(allow_null=True)
    createdAt = serializers.DateTimeField(allow_null=True)
    updatedAt = serializers.DateTimeField(allow_null=True)


class TrackerSyncLogSerializer(serializers.ModelSerializer):
    targetName = serializers.CharField(source="target_name")
    updatedAt = serializers.DateTimeField(source="updated_at")

    class Meta:
        model = TrackerSyncLog
        fields = ("id", "scope", "targetName", "status", "message", "updatedAt")
