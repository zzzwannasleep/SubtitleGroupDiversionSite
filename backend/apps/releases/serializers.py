from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.tracker_sync.serializers import TrackerSyncSnapshotSerializer, XbtFileSnapshotSerializer
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
        # Draft resources still need a stable display/sort timestamp for the current frontend contract.
        return (obj.published_at or obj.created_at).isoformat()


class ReleaseDetailSerializer(ReleaseSerializer):
    trackerSync = serializers.SerializerMethodField()
    xbtFile = serializers.SerializerMethodField()

    class Meta(ReleaseSerializer.Meta):
        fields = ReleaseSerializer.Meta.fields + ("trackerSync", "xbtFile")

    def _can_view_tracker_data(self, obj) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False
        return user.role == "admin" or obj.created_by_id == user.id

    def _get_sync_snapshot(self, obj):
        cache = getattr(self, "_sync_snapshot_cache", None)
        if cache is None:
            cache = {}
            self._sync_snapshot_cache = cache
        if obj.pk not in cache:
            from apps.tracker_sync.services import TrackerSyncService

            cache[obj.pk] = TrackerSyncService.get_release_sync_snapshot(obj)
        return cache[obj.pk]

    @extend_schema_field(TrackerSyncSnapshotSerializer)
    def get_trackerSync(self, obj):
        if not self._can_view_tracker_data(obj):
            return None
        return self._get_sync_snapshot(obj)["trackerSync"]

    @extend_schema_field(XbtFileSnapshotSerializer)
    def get_xbtFile(self, obj):
        if not self._can_view_tracker_data(obj):
            return None
        return self._get_sync_snapshot(obj)["xbtFile"]


class ReleaseWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    subtitle = serializers.CharField(max_length=255, allow_blank=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    categorySlug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.filter(is_active=True), source="category"
    )
    tagSlugs = serializers.SlugRelatedField(
        slug_field="slug", queryset=Tag.objects.all(), many=True, source="tags", required=False
    )
    torrentFile = serializers.FileField(source="torrent_file", required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Release._meta.get_field("status").choices, required=False)

    def validate(self, attrs):
        if self.instance is None and "torrent_file" not in attrs:
            raise serializers.ValidationError({"torrentFile": ["上传资源时必须提供 torrent 文件。"]})
        return attrs


class CategoryWriteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(max_length=100)

    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TagWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class ReleaseVisibilitySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("published", "published"), ("hidden", "hidden")])
