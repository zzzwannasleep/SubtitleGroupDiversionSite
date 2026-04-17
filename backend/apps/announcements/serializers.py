from urllib.parse import urlparse

from rest_framework import serializers

from apps.announcements.models import (
    Announcement,
    DEFAULT_LOGIN_BACKGROUND_CSS,
    LoginBackgroundType,
    SiteSetting,
)


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


class SiteSettingReadSerializer(serializers.ModelSerializer):
    siteName = serializers.CharField(source="site_name")
    siteDescription = serializers.CharField(source="site_description")
    loginNotice = serializers.CharField(source="login_notice")
    loginPageCss = serializers.CharField(source="login_page_css", allow_blank=True)
    allowPublicRegistration = serializers.BooleanField(source="allow_public_registration")
    rssBasePath = serializers.CharField(source="rss_base_path")
    downloadNotice = serializers.CharField(source="download_notice")
    siteIconUrl = serializers.CharField(source="site_icon_url", allow_blank=True)
    siteIconFileUrl = serializers.SerializerMethodField()
    siteIconResolvedUrl = serializers.SerializerMethodField()
    loginBackgroundType = serializers.ChoiceField(source="login_background_type", choices=LoginBackgroundType.choices)
    loginBackgroundApiUrl = serializers.CharField(source="login_background_api_url", allow_blank=True)
    loginBackgroundFileUrl = serializers.SerializerMethodField()
    loginBackgroundResolvedUrl = serializers.SerializerMethodField()
    loginBackgroundCss = serializers.CharField(source="login_background_css", allow_blank=True)

    class Meta:
        model = SiteSetting
        fields = (
            "siteName",
            "siteDescription",
            "loginNotice",
            "loginPageCss",
            "allowPublicRegistration",
            "rssBasePath",
            "downloadNotice",
            "siteIconUrl",
            "siteIconFileUrl",
            "siteIconResolvedUrl",
            "loginBackgroundType",
            "loginBackgroundApiUrl",
            "loginBackgroundFileUrl",
            "loginBackgroundResolvedUrl",
            "loginBackgroundCss",
        )

    def _absolute_url(self, value: str) -> str:
        if not value:
            return ""

        parsed = urlparse(value)
        if parsed.scheme or value.startswith("data:"):
            return value

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(value)

        return value

    def get_siteIconFileUrl(self, obj: SiteSetting) -> str:
        if not obj.site_icon_file:
            return ""
        return self._absolute_url(obj.site_icon_file.url)

    def get_siteIconResolvedUrl(self, obj: SiteSetting) -> str:
        return self.get_siteIconFileUrl(obj) or self._absolute_url(obj.site_icon_url)

    def get_loginBackgroundFileUrl(self, obj: SiteSetting) -> str:
        if not obj.login_background_file:
            return ""
        return self._absolute_url(obj.login_background_file.url)

    def get_loginBackgroundResolvedUrl(self, obj: SiteSetting) -> str:
        if obj.login_background_type == LoginBackgroundType.FILE:
            return self.get_loginBackgroundFileUrl(obj)
        if obj.login_background_type == LoginBackgroundType.API:
            return self._absolute_url(obj.login_background_api_url)
        return ""


class SiteSettingWriteSerializer(serializers.ModelSerializer):
    siteName = serializers.CharField(source="site_name", required=False, allow_blank=True, max_length=120)
    siteDescription = serializers.CharField(source="site_description", required=False, allow_blank=True, max_length=255)
    loginNotice = serializers.CharField(source="login_notice", required=False, allow_blank=True)
    loginPageCss = serializers.CharField(source="login_page_css", required=False, allow_blank=True)
    allowPublicRegistration = serializers.BooleanField(source="allow_public_registration", required=False)
    rssBasePath = serializers.CharField(source="rss_base_path", required=False, allow_blank=True, max_length=255)
    downloadNotice = serializers.CharField(source="download_notice", required=False, allow_blank=True)
    siteIconUrl = serializers.CharField(source="site_icon_url", required=False, allow_blank=True)
    siteIconFile = serializers.FileField(source="site_icon_file", required=False, allow_null=True, write_only=True)
    clearSiteIconFile = serializers.BooleanField(source="clear_site_icon_file", required=False, write_only=True)
    loginBackgroundType = serializers.ChoiceField(
        source="login_background_type",
        choices=LoginBackgroundType.choices,
        required=False,
    )
    loginBackgroundApiUrl = serializers.CharField(source="login_background_api_url", required=False, allow_blank=True)
    loginBackgroundFile = serializers.FileField(
        source="login_background_file",
        required=False,
        allow_null=True,
        write_only=True,
    )
    clearLoginBackgroundFile = serializers.BooleanField(
        source="clear_login_background_file",
        required=False,
        write_only=True,
    )
    loginBackgroundCss = serializers.CharField(source="login_background_css", required=False, allow_blank=True)

    class Meta:
        model = SiteSetting
        fields = (
            "siteName",
            "siteDescription",
            "loginNotice",
            "loginPageCss",
            "allowPublicRegistration",
            "rssBasePath",
            "downloadNotice",
            "siteIconUrl",
            "siteIconFile",
            "clearSiteIconFile",
            "loginBackgroundType",
            "loginBackgroundApiUrl",
            "loginBackgroundFile",
            "clearLoginBackgroundFile",
            "loginBackgroundCss",
        )

    def validate(self, attrs):
        instance = self.instance
        background_type = attrs.get(
            "login_background_type",
            getattr(instance, "login_background_type", LoginBackgroundType.CSS),
        )
        api_url = attrs.get("login_background_api_url", getattr(instance, "login_background_api_url", ""))
        css_value = attrs.get("login_background_css", getattr(instance, "login_background_css", DEFAULT_LOGIN_BACKGROUND_CSS))
        next_file = attrs.get("login_background_file")
        clear_file = attrs.get("clear_login_background_file", False)
        has_existing_file = bool(getattr(instance, "login_background_file", None)) and not clear_file

        if background_type == LoginBackgroundType.API and not api_url.strip():
            raise serializers.ValidationError({"loginBackgroundApiUrl": ["请选择 API 模式后填写可访问的图片地址。"]})

        if background_type == LoginBackgroundType.FILE and not (next_file or has_existing_file):
            raise serializers.ValidationError({"loginBackgroundFile": ["请选择文件模式并上传背景图。"]})

        if background_type == LoginBackgroundType.CSS and not css_value.strip():
            raise serializers.ValidationError({"loginBackgroundCss": ["请选择 CSS 模式并填写 background 样式值。"]})

        return attrs

    def update(self, instance: SiteSetting, validated_data):
        clear_site_icon_file = validated_data.pop("clear_site_icon_file", False)
        clear_login_background_file = validated_data.pop("clear_login_background_file", False)

        previous_site_icon_name = instance.site_icon_file.name if instance.site_icon_file else ""
        previous_background_name = instance.login_background_file.name if instance.login_background_file else ""

        if clear_site_icon_file:
            validated_data["site_icon_file"] = None

        if clear_login_background_file:
            validated_data["login_background_file"] = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if previous_site_icon_name and (
            clear_site_icon_file or ("site_icon_file" in validated_data and previous_site_icon_name != instance.site_icon_file.name)
        ):
            instance._meta.get_field("site_icon_file").storage.delete(previous_site_icon_name)

        if previous_background_name and (
            clear_login_background_file
            or ("login_background_file" in validated_data and previous_background_name != instance.login_background_file.name)
        ):
            instance._meta.get_field("login_background_file").storage.delete(previous_background_name)

        return instance
