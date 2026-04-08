from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.announcements.models import Announcement, SiteSetting
from apps.announcements.serializers import (
    AnnouncementSerializer,
    AnnouncementWriteSerializer,
    SiteSettingSerializer,
)
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response


def allowed_audiences_for_role(role: str):
    if role == "admin":
        return ["all", "uploader", "admin"]
    if role == "uploader":
        return ["all", "uploader"]
    return ["all"]


class VisibleAnnouncementListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = Announcement.objects.filter(
            status="online", audience__in=allowed_audiences_for_role(request.user.role)
        ).order_by("-updated_at", "-id")
        return success_response(AnnouncementSerializer(queryset, many=True).data)


class AdminAnnouncementListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(AnnouncementSerializer(Announcement.objects.all(), many=True).data)

    def post(self, request):
        if request.data.get("id"):
            announcement = get_object_or_404(Announcement, pk=request.data["id"])
            serializer = AnnouncementWriteSerializer(announcement, data=request.data, partial=True)
        else:
            serializer = AnnouncementWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()
        return success_response(AnnouncementSerializer(announcement).data, message="公告已保存。")


class SiteSettingView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(SiteSettingSerializer(SiteSetting.get_current()).data)

    def put(self, request):
        setting = SiteSetting.get_current()
        serializer = SiteSettingSerializer(setting, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, message="站点设置已保存。")
