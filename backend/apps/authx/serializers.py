from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    nextPassword = serializers.CharField(min_length=8)
