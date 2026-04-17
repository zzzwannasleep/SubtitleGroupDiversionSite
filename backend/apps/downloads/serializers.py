from rest_framework import serializers

from apps.downloads.models import DownloadLog


class DownloadLogSerializer(serializers.ModelSerializer):
    releaseId = serializers.IntegerField(source="release_id")
    releaseTitle = serializers.CharField(source="release.title")
    downloadedAt = serializers.DateTimeField(source="downloaded_at")
    downloaderId = serializers.IntegerField(source="user_id", allow_null=True)
    downloaderName = serializers.SerializerMethodField()

    class Meta:
        model = DownloadLog
        fields = ("id", "releaseId", "releaseTitle", "downloadedAt", "downloaderId", "downloaderName")

    def get_downloaderName(self, obj: DownloadLog) -> str:
        if not obj.user:
            return "匿名访问"
        return obj.user.display_name
