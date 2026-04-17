from rest_framework import serializers

from apps.downloads.models import DownloadLog


class DownloadLogSerializer(serializers.ModelSerializer):
    releaseId = serializers.IntegerField(source="release_id")
    releaseTitle = serializers.CharField(source="release.title")
    downloadedAt = serializers.DateTimeField(source="downloaded_at")
    downloaderId = serializers.IntegerField(source="user_id")
    downloaderName = serializers.CharField(source="user.display_name")

    class Meta:
        model = DownloadLog
        fields = ("id", "releaseId", "releaseTitle", "downloadedAt", "downloaderId", "downloaderName")
