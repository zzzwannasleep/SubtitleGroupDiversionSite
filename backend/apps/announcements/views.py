from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.views import APIView

from apps.announcements.models import Announcement, SiteSetting
from apps.announcements.serializers import (
    AnnouncementSerializer,
    AnnouncementWriteSerializer,
    SiteSettingSerializer,
)
from apps.audit.services import AuditService
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import success_response_schema


def allowed_audiences_for_role(role: str):
    if role == "admin":
        return ["all", "uploader", "admin"]
    if role == "uploader":
        return ["all", "uploader"]
    return ["all"]


@extend_schema_view(
    get=extend_schema(
        operation_id="announcements_visible_list",
        summary="获取当前用户可见公告",
        tags=["Announcements"],
        responses=success_response_schema("VisibleAnnouncementListResponse", AnnouncementSerializer(many=True)),
    ),
)
class VisibleAnnouncementListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = Announcement.objects.filter(
            status="online", audience__in=allowed_audiences_for_role(request.user.role)
        ).order_by("-updated_at", "-id")
        return success_response(AnnouncementSerializer(queryset, many=True).data)


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_announcements_list",
        summary="获取后台公告列表",
        tags=["Admin Announcements"],
        responses=success_response_schema("AdminAnnouncementListResponse", AnnouncementSerializer(many=True)),
    ),
    post=extend_schema(
        operation_id="admin_announcements_save",
        summary="创建或更新公告",
        tags=["Admin Announcements"],
        request=AnnouncementWriteSerializer,
        responses=success_response_schema("AdminAnnouncementSaveResponse", AnnouncementSerializer),
    ),
)
class AdminAnnouncementListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(AnnouncementSerializer(Announcement.objects.all(), many=True).data)

    def post(self, request):
        is_update = bool(request.data.get("id"))
        if request.data.get("id"):
            announcement = get_object_or_404(Announcement, pk=request.data["id"])
            serializer = AnnouncementWriteSerializer(announcement, data=request.data, partial=True)
        else:
            serializer = AnnouncementWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()
        AuditService.log(
            request.user,
            "更新公告" if is_update else "创建公告",
            "公告",
            announcement.title,
            detail=f"公告状态：{announcement.status}，可见范围：{announcement.audience}。",
            payload={"announcement_id": announcement.id},
        )
        return success_response(AnnouncementSerializer(announcement).data, message="公告已保存。")


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_settings_retrieve",
        summary="获取站点设置",
        tags=["Admin Settings"],
        responses=success_response_schema("AdminSiteSettingResponse", SiteSettingSerializer),
    ),
    put=extend_schema(
        operation_id="admin_settings_update",
        summary="更新站点设置",
        tags=["Admin Settings"],
        request=SiteSettingSerializer,
        responses=success_response_schema("AdminSiteSettingUpdateResponse", SiteSettingSerializer),
    ),
)
class SiteSettingView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(SiteSettingSerializer(SiteSetting.get_current()).data)

    def put(self, request):
        setting = SiteSetting.get_current()
        serializer = SiteSettingSerializer(setting, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.log(
            request.user,
            "更新站点设置",
            "站点设置",
            "基础配置",
            detail=f"RSS 基础路径更新为 {serializer.instance.rss_base_path}。",
            payload={"site_setting_id": setting.id},
        )
        return success_response(serializer.data, message="站点设置已保存。")
