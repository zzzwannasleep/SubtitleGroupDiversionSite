from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.models import InviteCode, User, UserRole, UserStatus


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
            "lastLoginAt",
            "joinedAt",
        )

    @extend_schema_field(serializers.DateTimeField())
    def get_lastLoginAt(self, obj) -> str:
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
    pass


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
    draftReleaseCount = serializers.IntegerField()
    activeAnnouncementCount = serializers.IntegerField()


class InviteCodeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="state")
    isActive = serializers.BooleanField(source="is_active")
    createdByName = serializers.SerializerMethodField()
    usedByName = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at")
    usedAt = serializers.DateTimeField(source="used_at", allow_null=True)
    expiresAt = serializers.DateTimeField(source="expires_at", allow_null=True)
    canRevoke = serializers.SerializerMethodField()

    class Meta:
        model = InviteCode
        fields = (
            "id",
            "code",
            "note",
            "status",
            "isActive",
            "createdByName",
            "usedByName",
            "createdAt",
            "usedAt",
            "expiresAt",
            "canRevoke",
        )

    @extend_schema_field(serializers.CharField())
    def get_createdByName(self, obj: InviteCode) -> str:
        if not obj.created_by:
            return "系统"
        return obj.created_by.display_name or obj.created_by.username

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_usedByName(self, obj: InviteCode) -> str | None:
        if not obj.used_by:
            return None
        return obj.used_by.display_name or obj.used_by.username

    @extend_schema_field(serializers.BooleanField())
    def get_canRevoke(self, obj: InviteCode) -> bool:
        return obj.state == "available"


class CreateInviteCodesSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=20, default=1)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expiresAt = serializers.DateTimeField(required=False, allow_null=True)

    def validate_expiresAt(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("过期时间必须晚于当前时间。")
        return value
