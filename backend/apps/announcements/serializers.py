from rest_framework import serializers

from apps.announcements.models import Announcement, SiteSetting


class AnnouncementSerializer(serializers.ModelSerializer):
    updatedAt = serializers.DateTimeField(source="updated_at")

    class Meta:
        model = Announcement
        fields = ("id", "title", "content", "status", "audience", "updatedAt")


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Announcement
        fields = ("id", "title", "content", "status", "audience")


class SiteSettingSerializer(serializers.ModelSerializer):
    siteName = serializers.CharField(source="site_name")
    siteDescription = serializers.CharField(source="site_description")
    loginNotice = serializers.CharField(source="login_notice")
    rssBasePath = serializers.CharField(source="rss_base_path")
    downloadNotice = serializers.CharField(source="download_notice")

    class Meta:
        model = SiteSetting
        fields = ("siteName", "siteDescription", "loginNotice", "rssBasePath", "downloadNotice")
