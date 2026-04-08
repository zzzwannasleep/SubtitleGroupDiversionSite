from rest_framework import serializers

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

    def get_lastLoginAt(self, obj):
        # Frontend date formatting assumes a string value, so we fall back to joined time
        # for users who have not logged in yet.
        return (obj.last_login or obj.date_joined).isoformat()


class AdminUserSerializer(CurrentUserSerializer):
    createdReleaseCount = serializers.SerializerMethodField()

    class Meta(CurrentUserSerializer.Meta):
        fields = CurrentUserSerializer.Meta.fields + ("createdReleaseCount",)

    def get_createdReleaseCount(self, obj):
        return getattr(obj, "created_release_count", None) or obj.created_releases.count()


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

    def get_trackerSync(self, obj):
        return self._get_sync_snapshot(obj)["trackerSync"]

    def get_xbtUser(self, obj):
        return self._get_sync_snapshot(obj)["xbtUser"]


class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    displayName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("该用户名已存在。")
        return value


class ChangeUserStatusSerializer(serializers.Serializer):
    nextStatus = serializers.ChoiceField(choices=UserStatus.choices)
