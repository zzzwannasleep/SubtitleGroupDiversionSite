from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.announcements.models import Announcement
from apps.audit.services import AuditService
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.releases.models import Release
from apps.releases.serializers import ReleaseSerializer
from apps.tracker_sync.models import TrackerSyncLog
from apps.tracker_sync.services import TrackerSyncService
from apps.users.models import User
from apps.users.serializers import AdminUserSerializer, ChangeUserStatusSerializer, CreateUserSerializer
from apps.users.services import UserService


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

    def get(self, request):
        keyword = (request.query_params.get("q") or "").strip()
        queryset = User.objects.annotate(created_release_count=Count("created_releases"))
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(display_name__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(role__icontains=keyword)
            )
        return success_response(AdminUserSerializer(queryset.order_by("-date_joined", "-id"), many=True).data)

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


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, user_id: int):
        user = get_object_or_404(User.objects.annotate(created_release_count=Count("created_releases")), pk=user_id)
        return success_response(AdminUserSerializer(user).data)


class AdminUserStatusView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        serializer = ChangeUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.change_status(actor=request.user, user=user, next_status=serializer.validated_data["nextStatus"])
        return success_response(AdminUserSerializer(user).data, message="用户状态已更新。")


class AdminUserResetPasskeyView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        user = UserService.reset_passkey(actor=request.user, user=user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


class SelfPasskeyResetView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        user = UserService.reset_passkey(actor=request.user, user=request.user)
        return success_response(AdminUserSerializer(user).data, message="passkey 已重置。")


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
