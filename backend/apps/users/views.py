from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework.views import APIView

from apps.announcements.models import Announcement
from apps.audit.services import AuditService
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.releases.models import Release
from apps.releases.serializers import ReleaseSerializer
from apps.tracker_sync.models import TrackerSyncLog
from apps.tracker_sync.serializers import TrackerSyncLogSerializer, TrackerSyncUserDetailSerializer
from apps.tracker_sync.services import TrackerSyncService
from apps.users.models import InviteCode, User, UserRole, UserStatus
from apps.users.serializers import (
    AdminDashboardStatsSerializer,
    AdminUserCreateSerializer,
    AdminUserDetailSerializer,
    AdminUserSerializer,
    ChangeUserStatusSerializer,
    CreateInviteCodesSerializer,
    CreateUserSerializer,
    InviteCodeSerializer,
    SelfApiTokenSerializer,
    SelfThemeSerializer,
    UpdateUserSerializer,
)
from apps.users.services import InviteCodeService, UserService


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_dashboard_overview",
        summary="获取后台仪表盘概览",
        tags=["Admin"],
        responses=success_response_schema(
            "AdminDashboardOverviewResponse",
            inline_serializer(
                name="AdminDashboardOverviewData",
                fields={
                    "stats": AdminDashboardStatsSerializer(),
                    "latestUsers": AdminUserSerializer(many=True),
                    "latestReleases": ReleaseSerializer(many=True),
                },
            ),
        ),
    ),
)
class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        latest_users = User.objects.annotate(created_release_count=Count("created_releases")).order_by(
            "-date_joined", "-id"
        )[:4]
        latest_releases = (
            Release.objects.select_related("category", "created_by")
            .prefetch_related("tags", "files")
            .order_by("-created_at", "-id")[:4]
        )
        stats = {
            "userCount": User.objects.count(),
            "releaseCount": Release.objects.count(),
            "activeReleaseCount": Release.objects.filter(status="published").count(),
            "pendingSyncCount": TrackerSyncLog.objects.filter(status__in=["warning", "failed"]).count(),
            "activeAnnouncementCount": Announcement.objects.filter(status="online").count(),
        }
        return success_response(
            {
                "stats": stats,
                "latestUsers": AdminUserSerializer(latest_users, many=True).data,
                "latestReleases": ReleaseSerializer(latest_releases, many=True).data,
            }
        )


class AdminUserListCreateView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(
        operation_id="admin_users_list",
        summary="获取用户列表",
        tags=["Admin Users"],
        parameters=[
            OpenApiParameter(name="q", description="按用户名、显示名、邮箱或角色搜索。", type=str),
            OpenApiParameter(name="role", description="按角色筛选。", enum=UserRole.values),
            OpenApiParameter(name="status", description="按状态筛选。", enum=UserStatus.values),
        ],
        responses=success_response_schema("AdminUserListResponse", AdminUserSerializer(many=True)),
    )
    def get(self, request):
        keyword = (request.query_params.get("q") or "").strip()
        role = (request.query_params.get("role") or "").strip()
        status = (request.query_params.get("status") or "").strip()
        queryset = User.objects.annotate(created_release_count=Count("created_releases"))

        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(display_name__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(role__icontains=keyword)
            )
        if role in UserRole.values:
            queryset = queryset.filter(role=role)
        if status in UserStatus.values:
            queryset = queryset.filter(status=status)

        return success_response(AdminUserSerializer(queryset.order_by("-date_joined", "-id"), many=True).data)

    @extend_schema(
        operation_id="admin_users_create",
        summary="创建用户",
        tags=["Admin Users"],
        request=CreateUserSerializer,
        responses=success_response_schema("AdminUserCreateResponse", AdminUserCreateSerializer),
    )
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, initial_password = UserService.create_user(
            actor=request.user,
            username=serializer.validated_data["username"],
            display_name=serializer.validated_data["displayName"],
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            password=serializer.validated_data.get("password") or None,
        )
        data = AdminUserSerializer(user).data
        if initial_password is not None:
            data["initialPassword"] = initial_password
        return success_response(data, message="用户创建成功。", status_code=201)


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_invite_codes_list",
        summary="获取邀请码列表",
        tags=["Admin Invite Codes"],
        responses=success_response_schema("AdminInviteCodeListResponse", InviteCodeSerializer(many=True)),
    ),
    post=extend_schema(
        operation_id="admin_invite_codes_create",
        summary="批量生成邀请码",
        tags=["Admin Invite Codes"],
        request=CreateInviteCodesSerializer,
        responses=success_response_schema("AdminInviteCodeCreateResponse", InviteCodeSerializer(many=True)),
    ),
)
class AdminInviteCodeListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = InviteCode.objects.select_related("created_by", "used_by").order_by("-created_at", "-id")
        return success_response(InviteCodeSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = CreateInviteCodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_codes = InviteCodeService.create_codes(
            actor=request.user,
            count=serializer.validated_data["count"],
            note=serializer.validated_data.get("note", ""),
            expires_at=serializer.validated_data.get("expiresAt"),
        )
        return success_response(
            InviteCodeSerializer(created_codes, many=True).data,
            message="邀请码已生成。",
            status_code=201,
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_invite_codes_revoke",
        summary="停用邀请码",
        tags=["Admin Invite Codes"],
        request=None,
        responses=success_response_schema("AdminInviteCodeRevokeResponse", InviteCodeSerializer),
    ),
)
class AdminInviteCodeRevokeView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, invite_code_id: int):
        invite_code = get_object_or_404(InviteCode, pk=invite_code_id)
        invite_code = InviteCodeService.revoke_code(actor=request.user, invite_code=invite_code)
        return success_response(InviteCodeSerializer(invite_code).data, message="邀请码已停用。")


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_users_detail",
        summary="获取用户详情",
        tags=["Admin Users"],
        responses=success_response_schema("AdminUserDetailResponse", AdminUserDetailSerializer),
    ),
    put=extend_schema(
        operation_id="admin_users_update",
        summary="更新用户基础信息",
        tags=["Admin Users"],
        request=UpdateUserSerializer,
        responses=success_response_schema("AdminUserUpdateResponse", AdminUserDetailSerializer),
    ),
    patch=extend_schema(
        operation_id="admin_users_partial_update",
        summary="更新用户基础信息",
        tags=["Admin Users"],
        request=UpdateUserSerializer,
        responses=success_response_schema("AdminUserPartialUpdateResponse", AdminUserDetailSerializer),
    ),
)
class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, user_id: int):
        user = get_object_or_404(User.objects.annotate(created_release_count=Count("created_releases")), pk=user_id)
        return success_response(AdminUserDetailSerializer(user).data)

    def put(self, request, user_id: int):
        return self._update(request, user_id, partial=False)

    def patch(self, request, user_id: int):
        return self._update(request, user_id, partial=True)

    def _update(self, request, user_id: int, *, partial: bool):
        user = get_object_or_404(User, pk=user_id)
        serializer = UpdateUserSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(
            actor=request.user,
            user=user,
            display_name=serializer.validated_data.get("displayName"),
            email=serializer.validated_data.get("email"),
            role=serializer.validated_data.get("role"),
        )
        refreshed = User.objects.annotate(created_release_count=Count("created_releases")).get(pk=user.pk)
        return success_response(AdminUserDetailSerializer(refreshed).data, message="用户信息已更新。")


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_users_change_status",
        summary="更新用户状态",
        tags=["Admin Users"],
        request=ChangeUserStatusSerializer,
        responses=success_response_schema("AdminUserStatusChangeResponse", AdminUserSerializer),
    ),
)
class AdminUserStatusView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        serializer = ChangeUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.change_status(actor=request.user, user=user, next_status=serializer.validated_data["nextStatus"])
        return success_response(AdminUserSerializer(user).data, message="用户状态已更新。")


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_users_disable",
        summary="禁用指定用户",
        tags=["Admin Users"],
        request=None,
        responses=success_response_schema("AdminUserDisableResponse", AdminUserSerializer),
    ),
)
class AdminUserDisableView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        user = UserService.change_status(actor=request.user, user=user, next_status="disabled")
        return success_response(AdminUserSerializer(user).data, message="用户已禁用。")


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_users_enable",
        summary="启用指定用户",
        tags=["Admin Users"],
        request=None,
        responses=success_response_schema("AdminUserEnableResponse", AdminUserSerializer),
    ),
)
class AdminUserEnableView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        user = UserService.change_status(actor=request.user, user=user, next_status="active")
        return success_response(AdminUserSerializer(user).data, message="用户已启用。")


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_users_reset_passkey",
        summary="重置指定用户 passkey",
        tags=["Admin Users"],
        request=None,
        responses=success_response_schema("AdminUserResetPasskeyResponse", AdminUserSerializer),
    ),
)
class AdminUserResetPasskeyView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        user = UserService.reset_passkey(actor=request.user, user=user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


@extend_schema_view(
    post=extend_schema(
        operation_id="users_reset_own_passkey",
        summary="重置当前登录用户 passkey",
        tags=["Users"],
        request=None,
        responses=success_response_schema("UserSelfResetPasskeyResponse", AdminUserSerializer),
    ),
)
class SelfPasskeyResetView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        user = UserService.reset_passkey(actor=request.user, user=request.user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


@extend_schema_view(
    get=extend_schema(
        operation_id="users_theme_retrieve",
        summary="获取当前用户主题",
        tags=["Users"],
        responses=success_response_schema("UserThemeResponse", SelfThemeSerializer),
    ),
    put=extend_schema(
        operation_id="users_theme_update",
        summary="更新当前用户主题",
        tags=["Users"],
        request=SelfThemeSerializer,
        responses=success_response_schema("UserThemeUpdateResponse", SelfThemeSerializer),
    ),
)
class SelfThemeView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(SelfThemeSerializer(request.user).data)

    def put(self, request):
        serializer = SelfThemeSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message="主题已保存。")


@extend_schema_view(
    get=extend_schema(
        operation_id="users_api_token_retrieve",
        summary="获取当前用户 API token",
        tags=["Users"],
        responses=success_response_schema("UserApiTokenResponse", SelfApiTokenSerializer),
    ),
    post=extend_schema(
        operation_id="users_api_token_reset",
        summary="重置当前用户 API token",
        tags=["Users"],
        request=None,
        responses=success_response_schema("UserApiTokenResetResponse", SelfApiTokenSerializer),
    ),
)
class SelfApiTokenView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(SelfApiTokenSerializer({"apiToken": request.user.api_token}).data)

    def post(self, request):
        user = UserService.reset_api_token(actor=request.user, user=request.user)
        return success_response(
            SelfApiTokenSerializer({"apiToken": user.api_token}).data,
            message="API token 已重置。",
        )


@extend_schema_view(
    get=extend_schema(
        operation_id="tracker_sync_user_detail",
        summary="获取指定用户的 XBT 同步详情",
        tags=["Tracker Sync"],
        responses=success_response_schema("TrackerSyncUserDetailResponse", TrackerSyncUserDetailSerializer),
    ),
    post=extend_schema(
        operation_id="tracker_sync_user_run",
        summary="手动同步指定用户到 XBT",
        tags=["Tracker Sync"],
        request=None,
        responses=success_response_schema("TrackerSyncUserActionResponse", TrackerSyncLogSerializer),
    ),
)
class AdminTrackerSyncUserView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        serializer = TrackerSyncUserDetailSerializer(TrackerSyncService.build_user_detail(user))
        return success_response(serializer.data)

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        log = TrackerSyncService.sync_user(user)
        AuditService.log(
            request.user,
            "手动同步用户到 XBT",
            "用户",
            user.username,
            detail=f"同步结果：{log.status}",
            payload={"user_id": user.id, "tracker_sync_log_id": log.id},
        )
        return success_response(TrackerSyncLogSerializer(log).data)
