from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.users.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    displayName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)
    confirmPassword = serializers.CharField(trim_whitespace=False)

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
