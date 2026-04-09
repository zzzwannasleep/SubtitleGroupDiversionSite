from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.common.pagination import StandardPageNumberPagination
from apps.common.permissions import IsActiveAuthenticated, IsAdminRole
from apps.common.responses import success_response
from apps.common.schema import paginated_success_response_schema, success_response_schema
from apps.releases.models import Category, Tag
from apps.releases.serializers import (
    CategorySerializer,
    CategoryWriteSerializer,
    ReleaseDetailSerializer,
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


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_home_data",
        summary="获取首页聚合数据",
        tags=["Releases"],
        responses=success_response_schema(
            "ReleaseHomeDataResponse",
            inline_serializer(
                name="ReleaseHomeData",
                fields={
                    "latestReleases": ReleaseSerializer(many=True),
                    "categories": CategorySerializer(many=True),
                    "tags": TagSerializer(many=True),
                },
            ),
        ),
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_categories_list",
        summary="获取分类列表",
        tags=["Releases"],
        responses=success_response_schema("ReleaseCategoryListResponse", CategorySerializer(many=True)),
    ),
)
class CategoryListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = Category.objects.filter(is_active=True).order_by("sort_order", "id")
        return success_response(CategorySerializer(queryset, many=True).data)


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_tags_list",
        summary="获取标签列表",
        tags=["Releases"],
        responses=success_response_schema("ReleaseTagListResponse", TagSerializer(many=True)),
    ),
)
class TagListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return success_response(TagSerializer(Tag.objects.order_by("name", "id"), many=True).data)


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_list",
        summary="获取资源列表",
        tags=["Releases"],
        parameters=[
            OpenApiParameter(name="q", description="资源关键词。", type=str),
            OpenApiParameter(name="category", description="分类 slug。", type=str),
            OpenApiParameter(name="tag", description="标签 slug。", type=str),
            OpenApiParameter(name="sort", description="排序方式。", enum=["latest", "downloads", "completions"]),
            OpenApiParameter(name="page", description="页码。", type=int),
            OpenApiParameter(name="pageSize", description="每页数量。", type=int),
        ],
        responses=paginated_success_response_schema("ReleaseListResponse", ReleaseSerializer),
    ),
    post=extend_schema(
        operation_id="releases_create",
        summary="创建资源",
        tags=["Releases"],
        request=ReleaseWriteSerializer,
        responses=success_response_schema("ReleaseCreateResponse", ReleaseSerializer),
    ),
)
class ReleaseCollectionView(ReleasePaginationMixin, APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

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


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_releases_list",
        summary="获取后台资源列表",
        tags=["Admin Releases"],
        parameters=[
            OpenApiParameter(name="status", description="资源状态筛选。", enum=["all", "draft", "published", "hidden"]),
            OpenApiParameter(name="page", description="页码。", type=int),
            OpenApiParameter(name="pageSize", description="每页数量。", type=int),
        ],
        responses=paginated_success_response_schema("AdminReleaseListResponse", ReleaseSerializer),
    ),
)
class AdminReleaseListView(ReleasePaginationMixin, APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = ReleaseService.query_releases(
            user=request.user, params=request.query_params, include_all_status=True
        )
        page = self.paginate_queryset(queryset)
        serializer = ReleaseSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        operation_id="releases_detail",
        summary="获取资源详情",
        tags=["Releases"],
        responses=success_response_schema("ReleaseDetailResponse", ReleaseDetailSerializer),
    ),
    patch=extend_schema(
        operation_id="releases_partial_update",
        summary="更新资源",
        tags=["Releases"],
        request=ReleaseWriteSerializer,
        responses=success_response_schema("ReleasePartialUpdateResponse", ReleaseSerializer),
    ),
    put=extend_schema(
        operation_id="releases_update",
        summary="更新资源",
        tags=["Releases"],
        request=ReleaseWriteSerializer,
        responses=success_response_schema("ReleaseUpdateResponse", ReleaseSerializer),
    ),
)
class ReleaseDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request, release_id: int):
        release = get_object_or_404(ReleaseService.base_queryset(), pk=release_id)
        ReleaseService.ensure_view_permission(user=request.user, release=release)
        return success_response(ReleaseDetailSerializer(release, context={"request": request}).data)

    def patch(self, request, release_id: int):
        return self._update(request, release_id)

    def put(self, request, release_id: int):
        return self._update(request, release_id)

    def _update(self, request, release_id: int):
        release = get_object_or_404(ReleaseService.base_queryset(), pk=release_id)
        if request.user.role not in {"admin", "uploader"}:
            raise PermissionDenied("仅上传者或管理员可编辑资源。")
        if request.user.role != "admin" and release.created_by_id != request.user.id:
            raise PermissionDenied("只能编辑自己发布的资源。")
        serializer = ReleaseWriteSerializer(instance=release, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        release = ReleaseService.update_release(actor=request.user, release=release, payload=serializer.validated_data)
        return success_response(ReleaseSerializer(release).data, message="资源更新成功。")


@extend_schema_view(
    post=extend_schema(
        operation_id="admin_releases_visibility_update",
        summary="切换资源可见状态",
        tags=["Admin Releases"],
        request=ReleaseVisibilitySerializer,
        responses=success_response_schema("ReleaseVisibilityResponse", ReleaseSerializer),
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        operation_id="users_releases_list",
        summary="获取我的发布",
        tags=["Releases"],
        responses=success_response_schema("MyReleaseListResponse", ReleaseSerializer(many=True)),
    ),
)
class MyReleaseListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        queryset = ReleaseService.base_queryset().filter(created_by=request.user).order_by("-created_at", "-id")
        return success_response(ReleaseSerializer(queryset, many=True).data)


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_categories_list",
        summary="获取后台分类列表",
        tags=["Admin Categories"],
        responses=success_response_schema("AdminCategoryListResponse", CategorySerializer(many=True)),
    ),
    post=extend_schema(
        operation_id="admin_categories_save",
        summary="创建或更新分类",
        tags=["Admin Categories"],
        request=CategoryWriteSerializer,
        responses=success_response_schema("AdminCategorySaveResponse", CategorySerializer),
    ),
)
class AdminCategoryListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(CategorySerializer(Category.objects.order_by("sort_order", "id"), many=True).data)

    def post(self, request):
        is_update = bool(request.data.get("id"))
        if request.data.get("id"):
            category = get_object_or_404(Category, pk=request.data["id"])
            serializer = CategoryWriteSerializer(category, data=request.data, partial=True)
        else:
            serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        AuditService.log(
            request.user,
            "更新分类" if is_update else "创建分类",
            "分类",
            category.name,
            detail=f"slug={category.slug}",
            payload={"category_id": category.id},
        )
        return success_response(CategorySerializer(category).data, message="分类已保存。")


@extend_schema_view(
    get=extend_schema(
        operation_id="admin_tags_list",
        summary="获取后台标签列表",
        tags=["Admin Tags"],
        responses=success_response_schema("AdminTagListResponse", TagSerializer(many=True)),
    ),
    post=extend_schema(
        operation_id="admin_tags_save",
        summary="创建或更新标签",
        tags=["Admin Tags"],
        request=TagWriteSerializer,
        responses=success_response_schema("AdminTagSaveResponse", TagSerializer),
    ),
)
class AdminTagListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return success_response(TagSerializer(Tag.objects.order_by("name", "id"), many=True).data)

    def post(self, request):
        is_update = bool(request.data.get("id"))
        if request.data.get("id"):
            tag = get_object_or_404(Tag, pk=request.data["id"])
            serializer = TagWriteSerializer(tag, data=request.data, partial=True)
        else:
            serializer = TagWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        AuditService.log(
            request.user,
            "更新标签" if is_update else "创建标签",
            "标签",
            tag.name,
            detail=f"slug={tag.slug}",
            payload={"tag_id": tag.id},
        )
        return success_response(TagSerializer(tag).data, message="标签已保存。")
