from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from apps.common.permissions import IsActiveAuthenticated
from apps.common.responses import success_response
from apps.common.throttles import RssFeedThrottle
from apps.releases.models import Category, Release, Tag
from apps.rss.services import RssService


@extend_schema_view(
    get=extend_schema(summary="获取 RSS 概览和订阅地址", tags=["RSS"]),
)
class RssOverviewView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(RssService.build_overview(request.user))


class BaseFeedView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [RssFeedThrottle]

    def get_user(self, request):
        passkey = request.query_params.get("passkey", "")
        user = RssService.resolve_passkey_user(passkey)
        if not user:
            raise PermissionDenied("passkey 无效或账户已禁用。")
        return user

    def render_feed(self, title, queryset, passkey):
        xml = RssService.build_feed(title, list(queryset), passkey)
        return HttpResponse(xml, content_type="application/rss+xml; charset=utf-8")


@extend_schema_view(
    get=extend_schema(
        summary="获取全部资源 RSS",
        tags=["RSS"],
        parameters=[OpenApiParameter(name="passkey", description="RSS 访问使用的 passkey。", type=str)],
    ),
)
class AllFeedView(BaseFeedView):
    def get(self, request):
        user = self.get_user(request)
        queryset = Release.objects.filter(status="published").order_by("-published_at", "-id")
        return self.render_feed("全部资源 RSS", queryset, user.passkey)


@extend_schema_view(
    get=extend_schema(
        summary="获取分类 RSS",
        tags=["RSS"],
        parameters=[OpenApiParameter(name="passkey", description="RSS 访问使用的 passkey。", type=str)],
    ),
)
class CategoryFeedView(BaseFeedView):
    def get(self, request, slug: str):
        user = self.get_user(request)
        category = get_object_or_404(Category, slug=slug, is_active=True)
        queryset = Release.objects.filter(status="published", category=category).order_by("-published_at", "-id")
        return self.render_feed(f"{category.name} RSS", queryset, user.passkey)


@extend_schema_view(
    get=extend_schema(
        summary="获取标签 RSS",
        tags=["RSS"],
        parameters=[OpenApiParameter(name="passkey", description="RSS 访问使用的 passkey。", type=str)],
    ),
)
class TagFeedView(BaseFeedView):
    def get(self, request, slug: str):
        user = self.get_user(request)
        tag = get_object_or_404(Tag, slug=slug)
        queryset = Release.objects.filter(status="published", tags=tag).order_by("-published_at", "-id").distinct()
        return self.render_feed(f"{tag.name} RSS", queryset, user.passkey)
