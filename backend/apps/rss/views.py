from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.responses import success_response
from apps.common.schema import success_response_schema
from apps.common.throttles import RssFeedThrottle
from apps.releases.models import Category, Release, Tag
from apps.rss.services import RssService


@extend_schema_view(
    get=extend_schema(
        operation_id="rss_overview",
        summary="获取 RSS 概览和订阅地址",
        tags=["RSS"],
        responses=success_response_schema(
            "RssOverviewResponse",
            inline_serializer(
                name="RssOverviewData",
                fields={
                    "generalFeed": serializers.URLField(),
                    "recentReleaseTitles": serializers.ListField(child=serializers.CharField()),
                },
            ),
        ),
    ),
)
class RssOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, _request):
        return success_response(RssService.build_overview())


class BaseFeedView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RssFeedThrottle]

    def render_feed(self, title, queryset):
        xml = RssService.build_feed(title, list(queryset))
        return HttpResponse(xml, content_type="application/rss+xml; charset=utf-8")


@extend_schema_view(
    get=extend_schema(
        operation_id="rss_all_feed",
        summary="获取全部资源 RSS",
        tags=["RSS"],
        responses={
            (200, "application/rss+xml"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="全部资源 RSS XML 内容。",
            )
        },
    ),
)
class AllFeedView(BaseFeedView):
    def get(self, request):
        queryset = Release.objects.filter(status="published").order_by("-published_at", "-id")
        return self.render_feed("全部资源 RSS", queryset)


@extend_schema_view(
    get=extend_schema(
        operation_id="rss_category_feed",
        summary="获取分类 RSS",
        tags=["RSS"],
        responses={
            (200, "application/rss+xml"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="分类 RSS XML 内容。",
            )
        },
    ),
)
class CategoryFeedView(BaseFeedView):
    def get(self, request, slug: str):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        queryset = Release.objects.filter(status="published", category=category).order_by("-published_at", "-id")
        return self.render_feed(f"{category.name} RSS", queryset)


@extend_schema_view(
    get=extend_schema(
        operation_id="rss_tag_feed",
        summary="获取标签 RSS",
        tags=["RSS"],
        responses={
            (200, "application/rss+xml"): OpenApiResponse(
                response=OpenApiTypes.STR,
                description="标签 RSS XML 内容。",
            )
        },
    ),
)
class TagFeedView(BaseFeedView):
    def get(self, request, slug: str):
        tag = get_object_or_404(Tag, slug=slug)
        queryset = Release.objects.filter(status="published", tags=tag).order_by("-published_at", "-id").distinct()
        return self.render_feed(f"{tag.name} RSS", queryset)

