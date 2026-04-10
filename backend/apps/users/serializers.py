from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.tracker_sync.serializers import TrackerSyncSnapshotSerializer, XbtUserSnapshotSerializer
from apps.users.models import User, UserRole, UserStatus


class UserSummarySerializer(serializers.ModelSerializer):
    displayName = serializers.CharField(source="display_name")

    class Meta:
        model = User
        fields = ("id", "username", "displayName", "role")


class CurrentUserSerializer(UserSummarySerializer):
    lastLoginAt = serializers.SerializerMethodField()
    joinedAt = serializers.DateTimeField(source="date_joined")

    class Meta(UserSummarySerializer.Meta):
        fields = UserSummarySerializer.Meta.fields + (
            "email",
            "status",
            "passkey",
            "lastLoginAt",
            "joinedAt",
        )

    @extend_schema_field(serializers.DateTimeField())
    def get_lastLoginAt(self, obj) -> str:
        # Frontend date formatting assumes a string value, so we fall back to joined time
        # for users who have not logged in yet.
        return (obj.last_login or obj.date_joined).isoformat()


class AdminUserSerializer(CurrentUserSerializer):
    createdReleaseCount = serializers.SerializerMethodField()

    class Meta(CurrentUserSerializer.Meta):
        fields = CurrentUserSerializer.Meta.fields + ("createdReleaseCount",)

    @extend_schema_field(serializers.IntegerField())
    def get_createdReleaseCount(self, obj) -> int:
        return getattr(obj, "created_release_count", None) or obj.created_releases.count()


class AdminUserCreateSerializer(AdminUserSerializer):
    initialPassword = serializers.CharField(allow_null=True, required=False)

    class Meta(AdminUserSerializer.Meta):
        fields = AdminUserSerializer.Meta.fields + ("initialPassword",)


class AdminUserDetailSerializer(AdminUserSerializer):
    trackerSync = serializers.SerializerMethodField()
    xbtUser = serializers.SerializerMethodField()

    class Meta(AdminUserSerializer.Meta):
        fields = AdminUserSerializer.Meta.fields + ("trackerSync", "xbtUser")

    def _get_sync_snapshot(self, obj):
        cache = getattr(self, "_sync_snapshot_cache", None)
        if cache is None:
            cache = {}
            self._sync_snapshot_cache = cache
        if obj.pk not in cache:
            from apps.tracker_sync.services import TrackerSyncService

            cache[obj.pk] = TrackerSyncService.get_user_sync_snapshot(obj)
        return cache[obj.pk]

    @extend_schema_field(TrackerSyncSnapshotSerializer)
    def get_trackerSync(self, obj):
        return self._get_sync_snapshot(obj)["trackerSync"]

    @extend_schema_field(XbtUserSnapshotSerializer)
    def get_xbtUser(self, obj):
        return self._get_sync_snapshot(obj)["xbtUser"]


class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    displayName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("该用户名已存在。")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        if not password:
            return attrs
        if not password.strip():
            raise serializers.ValidationError({"password": ["密码不能为空。"]})

        candidate_user = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            display_name=attrs.get("displayName", ""),
        )
        try:
            validate_password(password, user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


class UpdateUserSerializer(serializers.Serializer):
    displayName = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(choices=UserRole.choices, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("至少提供一个可更新字段。")
        return attrs


class ChangeUserStatusSerializer(serializers.Serializer):
    nextStatus = serializers.ChoiceField(choices=UserStatus.choices)


class SelfThemeSerializer(serializers.ModelSerializer):
    mode = serializers.ChoiceField(source="theme_mode", choices=["system", "light", "dark"])
    customCss = serializers.CharField(source="theme_custom_css", allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ("mode", "customCss")


class SelfApiTokenSerializer(serializers.Serializer):
    apiToken = serializers.CharField()


class AdminDashboardStatsSerializer(serializers.Serializer):
    userCount = serializers.IntegerField()
    releaseCount = serializers.IntegerField()
    activeReleaseCount = serializers.IntegerField()
    pendingSyncCount = serializers.IntegerField()
    activeAnnouncementCount = serializers.IntegerField()
