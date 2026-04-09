from django.contrib.auth import authenticate, login, logout
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.authx.serializers import ChangePasswordSerializer, LoginSerializer
from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.common.throttles import LoginRateThrottle
from apps.users.serializers import CurrentUserSerializer


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_login",
        summary="登录并建立 Session 会话",
        tags=["Auth"],
        request=LoginSerializer,
        responses=success_response_schema("AuthLoginResponse", CurrentUserSerializer),
    ),
)
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

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


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_logout",
        summary="退出当前会话",
        tags=["Auth"],
        request=None,
        responses=success_response_schema("AuthLogoutResponse"),
    ),
)
class LogoutView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        logout(request)
        return success_response(message="已退出登录。")


@extend_schema_view(
    get=extend_schema(
        operation_id="auth_me",
        summary="获取当前登录用户信息",
        tags=["Auth"],
        responses=success_response_schema("AuthMeResponse", CurrentUserSerializer),
    ),
)
class MeView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(CurrentUserSerializer(request.user).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_change_password",
        summary="修改当前登录用户密码",
        tags=["Auth"],
        request=ChangePasswordSerializer,
        responses=success_response_schema("AuthChangePasswordResponse"),
    ),
)
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
