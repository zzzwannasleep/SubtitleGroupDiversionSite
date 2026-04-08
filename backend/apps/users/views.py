from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.views import APIView

from apps.announcements.models import Announcement
from apps.audit.services import AuditService
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.releases.models import Release
from apps.releases.serializers import ReleaseSerializer
from apps.tracker_sync.models import TrackerSyncLog
from apps.tracker_sync.services import TrackerSyncService
from apps.users.models import User, UserRole, UserStatus
from apps.users.serializers import AdminUserDetailSerializer, AdminUserSerializer, ChangeUserStatusSerializer, CreateUserSerializer
from apps.users.services import UserService


@extend_schema_view(
    get=extend_schema(summary="获取后台仪表盘概览", tags=["Admin"]),
)
class AdminDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        latest_users = User.objects.annotate(created_release_count=Count("created_releases")).order_by("-date_joined", "-id")[:4]
        latest_releases = Release.objects.select_related("category", "created_by").prefetch_related("tags", "files").order_by(
            "-created_at", "-id"
        )[:4]
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
        summary="获取用户列表",
        tags=["Admin Users"],
        parameters=[
            OpenApiParameter(name="q", description="关键词，支持用户名、显示名、邮箱和角色搜索。", type=str),
            OpenApiParameter(name="role", description="按角色筛选。", enum=UserRole.values),
            OpenApiParameter(name="status", description="按状态筛选。", enum=UserStatus.values),
        ],
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

    @extend_schema(summary="创建用户", tags=["Admin Users"])
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, initial_password = UserService.create_user(
            actor=request.user,
            username=serializer.validated_data["username"],
            display_name=serializer.validated_data["displayName"],
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
        )
        data = AdminUserSerializer(user).data
        data["initialPassword"] = initial_password
        return success_response(data, message="用户创建成功。", status_code=201)


@extend_schema_view(
    get=extend_schema(summary="获取用户详情", tags=["Admin Users"]),
)
class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, user_id: int):
        user = get_object_or_404(User.objects.annotate(created_release_count=Count("created_releases")), pk=user_id)
        return success_response(AdminUserDetailSerializer(user).data)


@extend_schema_view(
    post=extend_schema(summary="更新用户状态", tags=["Admin Users"]),
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
    post=extend_schema(summary="重置指定用户 passkey", tags=["Admin Users"]),
)
class AdminUserResetPasskeyView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        user = UserService.reset_passkey(actor=request.user, user=user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


@extend_schema_view(
    post=extend_schema(summary="重置当前登录用户 passkey", tags=["Users"]),
)
class SelfPasskeyResetView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        user = UserService.reset_passkey(actor=request.user, user=request.user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


@extend_schema_view(
    post=extend_schema(summary="手动同步指定用户到 XBT", tags=["Tracker Sync"]),
)
class AdminTrackerSyncUserView(APIView):
    permission_classes = [IsAdminRole]

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
        return success_response({"logId": log.id, "status": log.status, "message": log.message})
