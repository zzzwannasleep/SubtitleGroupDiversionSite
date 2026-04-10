from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.announcements.models import SiteSetting
from apps.authx.serializers import ChangePasswordSerializer, LoginSerializer, RegisterSerializer
from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.common.throttles import LoginRateThrottle
from apps.users.serializers import CurrentUserSerializer
from apps.users.services import InviteCodeService, UserService


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
            raise PermissionDenied("当前账号已被禁用。")
        login(request, user)
        return success_response(CurrentUserSerializer(user).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="auth_register",
        summary="注册普通用户账号",
        tags=["Auth"],
        request=RegisterSerializer,
        responses=success_response_schema("AuthRegisterResponse", CurrentUserSerializer),
    ),
)
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        settings = SiteSetting.get_current()
        serializer = RegisterSerializer(
            data=request.data,
            context={"requires_invite": not settings.allow_public_registration},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user, _ = UserService.create_user(
                actor=None,
                username=serializer.validated_data["username"],
                display_name=serializer.validated_data["displayName"],
                email=serializer.validated_data["email"],
                role="user",
                password=serializer.validated_data["password"],
            )
            if serializer.validated_data["inviteCode"]:
                InviteCodeService.redeem_code(raw_code=serializer.validated_data["inviteCode"], user=user)

        login(request, user)
        return success_response(CurrentUserSerializer(user).data, message="注册成功。", status_code=201)


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
