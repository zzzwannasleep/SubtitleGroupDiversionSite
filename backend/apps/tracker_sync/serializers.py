from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.tracker_sync.models import TrackerSyncLog, TrackerSyncScope


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
    userId = serializers.IntegerField(source="user_id", allow_null=True)
    releaseId = serializers.IntegerField(source="release_id", allow_null=True)
    retryable = serializers.SerializerMethodField()

    class Meta:
        model = TrackerSyncLog
        fields = ("id", "scope", "targetName", "status", "message", "updatedAt", "userId", "releaseId", "retryable")

    @extend_schema_field(serializers.BooleanField())
    def get_retryable(self, obj):
        if obj.scope == TrackerSyncScope.FULL:
            return True
        if obj.scope == TrackerSyncScope.USER:
            return obj.user_id is not None
        if obj.scope == TrackerSyncScope.RELEASE:
            return obj.release_id is not None
        return False


class TrackerSyncOverviewSummarySerializer(serializers.Serializer):
    xbtSyncEnabled = serializers.BooleanField()
    xbtDatabaseAlias = serializers.CharField()
    totalLogs = serializers.IntegerField()
    successCount = serializers.IntegerField()
    warningCount = serializers.IntegerField()
    failedCount = serializers.IntegerField()
    pendingCount = serializers.IntegerField()
    lastSuccessAt = serializers.DateTimeField(allow_null=True)
    lastFailureAt = serializers.DateTimeField(allow_null=True)
    lastFullSyncAt = serializers.DateTimeField(allow_null=True)


class TrackerSyncOverviewSerializer(serializers.Serializer):
    summary = TrackerSyncOverviewSummarySerializer()
    latestLogs = TrackerSyncLogSerializer(many=True)
    failedLogs = TrackerSyncLogSerializer(many=True)


class TrackerSyncUserTargetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    displayName = serializers.CharField()
    role = serializers.CharField()
    status = serializers.CharField()
    passkey = serializers.CharField()


class TrackerSyncUserDetailSerializer(serializers.Serializer):
    user = TrackerSyncUserTargetSerializer()
    trackerSync = TrackerSyncSnapshotSerializer(allow_null=True)
    xbtUser = XbtUserSnapshotSerializer()
    recentLogs = TrackerSyncLogSerializer(many=True)


class TrackerSyncReleaseTargetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    infohash = serializers.CharField()
    publishedAt = serializers.DateTimeField()
    createdById = serializers.IntegerField()


class TrackerSyncReleaseDetailSerializer(serializers.Serializer):
    release = TrackerSyncReleaseTargetSerializer()
    trackerSync = TrackerSyncSnapshotSerializer(allow_null=True)
    xbtFile = XbtFileSnapshotSerializer()
    recentLogs = TrackerSyncLogSerializer(many=True)
