from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        db_table = "tags"
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class ReleaseStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    PUBLISHED = "published", "已发布"
    HIDDEN = "hidden", "已隐藏"


class Release(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="releases")
    tags = models.ManyToManyField(Tag, related_name="releases", blank=True)
    status = models.CharField(max_length=20, choices=ReleaseStatus.choices, default=ReleaseStatus.DRAFT)
    cover_image_url = models.URLField(blank=True)
    size_bytes = models.BigIntegerField(default=0)
    infohash = models.CharField(max_length=40, unique=True)
    torrent_file = models.FileField(upload_to="torrent_templates/")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_releases"
    )
    download_count = models.PositiveIntegerField(default=0)
    completion_count = models.PositiveIntegerField(default=0)
    active_peers = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "releases"
        ordering = ["-published_at", "-created_at", "-id"]

    def __str__(self) -> str:
        return self.title


class ReleaseFile(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="files")
    file_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField(default=0)

    class Meta:
        db_table = "release_files"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.file_path
