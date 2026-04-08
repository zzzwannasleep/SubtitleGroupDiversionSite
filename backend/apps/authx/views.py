from django.contrib.auth import authenticate, login, logout
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.authx.serializers import ChangePasswordSerializer, LoginSerializer
from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.users.serializers import CurrentUserSerializer


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            raise AuthenticationFailed("用户名或密码错误。")
        if user.status != "active":
            raise PermissionDenied("当前账户已被禁用。")
        login(request, user)
        return success_response(CurrentUserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        logout(request)
        return success_response(message="已退出登录。")


class MeView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(CurrentUserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_password = serializer.validated_data["currentPassword"]
        next_password = serializer.validated_data["nextPassword"]
        if not request.user.check_password(current_password):
            raise PermissionDenied("当前密码不正确。")
        request.user.set_password(next_password)
        request.user.save(update_fields=["password"])
        login(request, request.user)
        return success_response(message="密码修改成功。")
