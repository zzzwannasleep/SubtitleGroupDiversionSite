from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.users.models import INVITE_CODE_LENGTH, User, compact_invite_code, normalize_invite_code


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    displayName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)
    confirmPassword = serializers.CharField(trim_whitespace=False)
    inviteCode = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("请输入用户名。")
        if User.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError("该用户名已存在。")
        return normalized

    def validate_displayName(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("请输入显示名称。")
        return normalized

    def validate(self, attrs):
        password = attrs["password"]
        confirm_password = attrs["confirmPassword"]
        invite_code = attrs.get("inviteCode", "")
        requires_invite = bool(self.context.get("requires_invite"))

        if requires_invite and not invite_code.strip():
            raise serializers.ValidationError("当前站点仅支持邀请码注册，请输入邀请码。")

        if invite_code.strip():
            compact_code = compact_invite_code(invite_code)
            if len(compact_code) != INVITE_CODE_LENGTH:
                raise serializers.ValidationError("邀请码格式不正确。")
            attrs["inviteCode"] = normalize_invite_code(invite_code)
        else:
            attrs["inviteCode"] = ""

        if not password.strip():
            raise serializers.ValidationError({"password": ["请输入密码。"]})

        if password != confirm_password:
            raise serializers.ValidationError({"confirmPassword": ["两次输入的密码不一致。"]})

        candidate_user = User(
            username=attrs["username"],
            email=attrs["email"],
            display_name=attrs["displayName"],
        )

        try:
            validate_password(password, user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    nextPassword = serializers.CharField(min_length=8)
