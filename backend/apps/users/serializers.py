from rest_framework import serializers

from apps.users.models import User, UserRole, UserStatus


class UserSummarySerializer(serializers.ModelSerializer):
    displayName = serializers.CharField(source="display_name")

    class Meta:
        model = User
        fields = ("id", "username", "displayName", "role")


class CurrentUserSerializer(UserSummarySerializer):
    lastLoginAt = serializers.DateTimeField(source="last_login", allow_null=True)
    joinedAt = serializers.DateTimeField(source="date_joined")

    class Meta(UserSummarySerializer.Meta):
        fields = UserSummarySerializer.Meta.fields + (
            "email",
            "status",
            "passkey",
            "lastLoginAt",
            "joinedAt",
        )


class AdminUserSerializer(CurrentUserSerializer):
    createdReleaseCount = serializers.SerializerMethodField()

    class Meta(CurrentUserSerializer.Meta):
        fields = CurrentUserSerializer.Meta.fields + ("createdReleaseCount",)

    def get_createdReleaseCount(self, obj):
        return getattr(obj, "created_release_count", None) or obj.created_releases.count()


class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    displayName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices)


class ChangeUserStatusSerializer(serializers.Serializer):
    nextStatus = serializers.ChoiceField(choices=UserStatus.choices)
