from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.releases.models import Category, Release, ReleaseFile, Tag
from apps.users.serializers import UserSummarySerializer


class CategorySerializer(serializers.ModelSerializer):
    sortOrder = serializers.IntegerField(source="sort_order")
    isActive = serializers.BooleanField(source="is_active")

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "sortOrder", "isActive")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class ReleaseFileSerializer(serializers.ModelSerializer):
    path = serializers.CharField(source="file_path")
    sizeBytes = serializers.IntegerField(source="file_size")

    class Meta:
        model = ReleaseFile
        fields = ("path", "sizeBytes")


class ReleaseSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    createdBy = UserSummarySerializer(source="created_by")
    files = ReleaseFileSerializer(many=True)
    sizeBytes = serializers.IntegerField(source="size_bytes")
    coverImageUrl = serializers.CharField(source="cover_image_url", allow_blank=True)
    publishedAt = serializers.SerializerMethodField()
    updatedAt = serializers.DateTimeField(source="updated_at")
    downloadCount = serializers.IntegerField(source="download_count")
    completionCount = serializers.IntegerField(source="completion_count")
    activePeers = serializers.IntegerField(source="active_peers")

    class Meta:
        model = Release
        fields = (
            "id",
            "title",
            "subtitle",
            "description",
            "category",
            "tags",
            "status",
            "sizeBytes",
            "infohash",
            "coverImageUrl",
            "publishedAt",
            "updatedAt",
            "createdBy",
            "files",
            "downloadCount",
            "completionCount",
            "activePeers",
        )

    @extend_schema_field(serializers.DateTimeField())
    def get_publishedAt(self, obj) -> str:
        return (obj.published_at or obj.created_at).isoformat()


class ReleaseDetailSerializer(ReleaseSerializer):
    pass


class ReleaseWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_blank=True, required=False)
    subtitle = serializers.CharField(max_length=255, allow_blank=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    categorySlug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.filter(is_active=True),
        source="category",
        required=False,
    )
    tagSlugs = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Tag.objects.all(),
        many=True,
        source="tags",
        required=False,
    )
    torrentFile = serializers.FileField(source="torrent_file", required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Release._meta.get_field("status").choices, required=False)

    def validate(self, attrs):
        if self.instance is None and "torrent_file" not in attrs:
            raise serializers.ValidationError({"torrentFile": ["上传资源时必须提供 torrent 文件。"]})
        if self.instance is not None and "title" in attrs and not attrs["title"]:
            raise serializers.ValidationError({"title": ["编辑资源时标题不能为空。"]})
        return attrs


class CategoryWriteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(max_length=100)
    sortOrder = serializers.IntegerField(source="sort_order", min_value=1, required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "sortOrder", "isActive")


class TagWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class ReleaseVisibilitySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("published", "published"), ("hidden", "hidden")])
