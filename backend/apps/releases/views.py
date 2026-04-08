from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from apps.common.pagination import StandardPageNumberPagination
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.releases.models import Category, Tag
from apps.releases.serializers import (
    CategorySerializer,
    CategoryWriteSerializer,
    ReleaseSerializer,
    ReleaseVisibilitySerializer,
    ReleaseWriteSerializer,
    TagSerializer,
    TagWriteSerializer,
)
from apps.releases.services import ReleaseService


class ReleasePaginationMixin:
    paginator = None

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            self.paginator = StandardPageNumberPagination()
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)


class HomeDataView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        latest_releases = ReleaseService.base_queryset().filter(status="published").order_by("-published_at", "-id")[:5]
        categories = Category.objects.filter(is_active=True).order_by("sort_order", "id")
        tags = Tag.objects.order_by("name", "id")
        return success_response(
            {
                "latestReleases": ReleaseSerializer(latest_releases, many=True).data,
                "categories": CategorySerializer(categories, many=True).data,
                "tags": TagSerializer(tags, many=True).data,
            }
        )


class CategoryListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = Category.objects.filter(is_active=True).order_by("sort_order", "id")
        return success_response(CategorySerializer(queryset, many=True).data)


class TagListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(TagSerializer(Tag.objects.order_by("name", "id"), many=True).data)


class ReleaseCollectionView(ReleasePaginationMixin, APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = ReleaseService.query_releases(user=request.user, params=request.query_params)
        page = self.paginate_queryset(queryset)
        serializer = ReleaseSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        if request.user.role not in {"admin", "uploader"}:
            raise PermissionDenied("仅上传者或管理员可发布资源。")
        serializer = ReleaseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        release = ReleaseService.create_release(actor=request.user, payload=serializer.validated_data)
        return success_response(ReleaseSerializer(release).data, message="资源创建成功。", status_code=201)


class AdminReleaseListView(ReleasePaginationMixin, APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = ReleaseService.query_releases(
            user=request.user, params=request.query_params, include_all_status=True
        )
        page = self.paginate_queryset(queryset)
        serializer = ReleaseSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ReleaseDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, release_id: int):
        release = get_object_or_404(ReleaseService.base_queryset(), pk=release_id)
        ReleaseService.ensure_view_permission(user=request.user, release=release)
        return success_response(ReleaseSerializer(release).data)

    def patch(self, request, release_id: int):
        release = get_object_or_404(ReleaseService.base_queryset(), pk=release_id)
        if request.user.role not in {"admin", "uploader"}:
            raise PermissionDenied("仅上传者或管理员可编辑资源。")
        if request.user.role != "admin" and release.created_by_id != request.user.id:
            raise PermissionDenied("只能编辑自己发布的资源。")
        serializer = ReleaseWriteSerializer(instance=release, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        release = ReleaseService.update_release(actor=request.user, release=release, payload=serializer.validated_data)
        return success_response(ReleaseSerializer(release).data, message="资源更新成功。")

    put = patch


class ReleaseVisibilityView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, release_id: int):
        release = get_object_or_404(ReleaseService.base_queryset(), pk=release_id)
        serializer = ReleaseVisibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        release = ReleaseService.set_visibility(
            actor=request.user, release=release, status=serializer.validated_data["status"]
        )
        return success_response(ReleaseSerializer(release).data, message="资源状态已更新。")


class MyReleaseListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = ReleaseService.base_queryset().filter(created_by=request.user).order_by("-created_at", "-id")
        return success_response(ReleaseSerializer(queryset, many=True).data)


class AdminCategoryListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(CategorySerializer(Category.objects.order_by("sort_order", "id"), many=True).data)

    def post(self, request):
        if request.data.get("id"):
            category = get_object_or_404(Category, pk=request.data["id"])
            serializer = CategoryWriteSerializer(category, data=request.data, partial=True)
        else:
            serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return success_response(CategorySerializer(category).data, message="分类已保存。")


class AdminTagListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(TagSerializer(Tag.objects.order_by("name", "id"), many=True).data)

    def post(self, request):
        if request.data.get("id"):
            tag = get_object_or_404(Tag, pk=request.data["id"])
            serializer = TagWriteSerializer(tag, data=request.data, partial=True)
        else:
            serializer = TagWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        return success_response(TagSerializer(tag).data, message="标签已保存。")
