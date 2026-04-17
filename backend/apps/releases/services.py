from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.audit.services import AuditService
from apps.common.exceptions import BusinessException
from apps.common.torrent import parse_torrent
from apps.releases.models import Category, Release, ReleaseFile, ReleaseStatus


class ReleaseService:
    @staticmethod
    def base_queryset():
        return Release.objects.select_related("category", "created_by").prefetch_related("tags", "files")

    @classmethod
    def query_releases(cls, *, user=None, params=None, include_all_status=False):
        params = params or {}
        queryset = cls.base_queryset()
        if not include_all_status:
            queryset = queryset.filter(status=ReleaseStatus.PUBLISHED)

        keyword = (params.get("q") or "").strip()
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(subtitle__icontains=keyword)
                | Q(description__icontains=keyword)
            )

        if params.get("category"):
            queryset = queryset.filter(category__slug=params["category"])
        if params.get("tag"):
            queryset = queryset.filter(tags__slug=params["tag"])
        if params.get("ownerId"):
            queryset = queryset.filter(created_by_id=params["ownerId"])
        status = params.get("status")
        if status and status != "all":
            queryset = queryset.filter(status=status)

        sort = params.get("sort", "latest")
        if sort == "downloads":
            queryset = queryset.order_by("-download_count", "-published_at", "-id")
        elif sort == "completions":
            queryset = queryset.order_by("-completion_count", "-published_at", "-id")
        else:
            queryset = queryset.order_by("-published_at", "-created_at", "-id")
        return queryset.distinct()

    @staticmethod
    def ensure_view_permission(*, user, release: Release):
        if release.status == ReleaseStatus.PUBLISHED:
            return
        if user.role == "admin" or release.created_by_id == user.id:
            return
        raise PermissionDenied("你没有权限查看该资源。")

    @staticmethod
    def _apply_torrent_payload(release: Release, torrent_file):
        original_name = getattr(torrent_file, "name", "upload.torrent")
        torrent_bytes = torrent_file.read()
        metadata = parse_torrent(torrent_bytes)
        duplicated = Release.objects.exclude(pk=release.pk).filter(infohash=metadata.infohash).exists()
        if duplicated:
            raise BusinessException("该 infohash 已存在，不能重复发布。")

        release.size_bytes = metadata.size_bytes
        release.infohash = metadata.infohash
        stored_torrent = ContentFile(torrent_bytes)
        stored_torrent.name = original_name
        release.torrent_file = stored_torrent
        return metadata

    @staticmethod
    def _get_default_category():
        category = Category.objects.filter(is_active=True).order_by("sort_order", "id").first()
        if category is None:
            raise BusinessException("当前没有可用分类，请先在后台创建并启用至少一个分类。")
        return category

    @staticmethod
    def _build_default_title(*, payload: dict, torrent_file, metadata) -> str:
        explicit_title = (payload.get("title") or "").strip()
        if explicit_title:
            return explicit_title

        metadata_name = (metadata.name or "").strip()
        if metadata_name:
            return metadata_name

        original_name = Path(getattr(torrent_file, "name", "upload.torrent")).stem.strip()
        if original_name:
            return original_name

        return f"资源 {metadata.infohash[:8]}"

    @classmethod
    @transaction.atomic
    def create_release(cls, *, actor, payload: dict):
        payload = dict(payload)
        tags = payload.pop("tags", [])
        torrent_file = payload.pop("torrent_file")
        status = payload.get("status", ReleaseStatus.PUBLISHED)

        release = Release(created_by=actor)
        metadata = cls._apply_torrent_payload(release, torrent_file)
        release.title = cls._build_default_title(payload=payload, torrent_file=torrent_file, metadata=metadata)
        release.subtitle = payload.get("subtitle", "")
        release.description = payload.get("description", "")
        release.category = payload.get("category") or cls._get_default_category()
        release.status = status
        if status == ReleaseStatus.PUBLISHED and not release.published_at:
            release.published_at = timezone.now()
        release.save()
        if tags:
            release.tags.set(tags)
        ReleaseFile.objects.bulk_create(
            [
                ReleaseFile(release=release, file_path=item.path, file_size=item.size_bytes)
                for item in metadata.files
            ]
        )
        AuditService.log(
            actor,
            "发布资源",
            "资源",
            release.title,
            detail="上传 torrent 并写入文件列表。",
            payload={"release_id": release.id},
        )
        return release

    @classmethod
    @transaction.atomic
    def update_release(cls, *, actor, release: Release, payload: dict):
        tags = payload.pop("tags", None)
        torrent_file = payload.pop("torrent_file", None)
        for field, value in payload.items():
            setattr(release, field, value)
        if release.status == ReleaseStatus.PUBLISHED and not release.published_at:
            release.published_at = timezone.now()
        if torrent_file:
            metadata = cls._apply_torrent_payload(release, torrent_file)
            release.save()
            release.files.all().delete()
            ReleaseFile.objects.bulk_create(
                [
                    ReleaseFile(release=release, file_path=item.path, file_size=item.size_bytes)
                    for item in metadata.files
                ]
            )
        else:
            release.save()
        if tags is not None:
            release.tags.set(tags)
        AuditService.log(
            actor,
            "编辑资源",
            "资源",
            release.title,
            detail="资源元数据已更新。",
            payload={"release_id": release.id},
        )
        return release

    @classmethod
    @transaction.atomic
    def set_visibility(cls, *, actor, release: Release, status: str):
        release.status = status
        if status == ReleaseStatus.PUBLISHED and not release.published_at:
            release.published_at = timezone.now()
        release.save(update_fields=["status", "published_at", "updated_at"])
        AuditService.log(
            actor,
            "恢复资源" if status == ReleaseStatus.PUBLISHED else "隐藏资源",
            "资源",
            release.title,
            detail=f"资源状态切换为 {status}。",
            payload={"release_id": release.id},
        )
        return release
