from pathlib import Path, PurePosixPath

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.audit.services import AuditService
from apps.common.exceptions import BusinessException
from apps.common.torrent import parse_torrent
from apps.releases.models import Category, Release, ReleaseFile, ReleaseStatus, ReleaseWebseedFile
from apps.tracker.services import TrackerService, TrackerSyncService


class ReleaseService:
    @staticmethod
    def base_queryset():
        return Release.objects.select_related("category", "created_by", "tracker_sync").prefetch_related(
            "tags", "files", "webseed_files"
        )

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
        normalized_torrent_bytes = TrackerService.normalize_uploaded_torrent(torrent_bytes)
        metadata = parse_torrent(normalized_torrent_bytes)
        duplicated = Release.objects.exclude(pk=release.pk).filter(infohash=metadata.infohash).exists()
        if duplicated:
            raise BusinessException("该 infohash 已存在，不能重复发布。")

        release.size_bytes = metadata.size_bytes
        release.infohash = metadata.infohash
        stored_torrent = ContentFile(normalized_torrent_bytes)
        stored_torrent.name = original_name
        release.torrent_file = stored_torrent
        return metadata

    @staticmethod
    def _normalize_relative_path(value: str) -> str:
        normalized = str(value or "").strip().replace("\\", "/").lstrip("/")
        if not normalized:
            return ""

        parts: list[str] = []
        for part in PurePosixPath(normalized).parts:
            if part in {"", "."}:
                continue
            if part == "..":
                raise BusinessException("分流文件路径不合法，不能包含上级目录。")
            parts.append(part)
        return "/".join(parts)

    @classmethod
    def _strip_leading_segments(cls, value: str, count: int) -> str:
        normalized = cls._normalize_relative_path(value)
        if not normalized or count <= 0:
            return normalized

        parts = list(PurePosixPath(normalized).parts)
        if len(parts) <= count:
            return ""
        return "/".join(parts[count:])

    @classmethod
    def _build_webseed_path_candidates(cls, normalized_entries: list[tuple[object, str]]) -> list[dict[str, object]]:
        if not normalized_entries:
            return []

        segment_lengths = [len(PurePosixPath(path).parts) for _, path in normalized_entries]
        max_strip_count = max(min(segment_lengths) - 1, 0)
        candidates: list[dict[str, object]] = []

        for strip_count in range(max_strip_count + 1):
            candidate_entries: dict[str, object] = {}
            valid = True
            for upload_file, normalized_path in normalized_entries:
                candidate_path = cls._strip_leading_segments(normalized_path, strip_count)
                if not candidate_path or candidate_path in candidate_entries:
                    valid = False
                    break
                candidate_entries[candidate_path] = upload_file
            if valid:
                candidates.append(candidate_entries)
        return candidates

    @classmethod
    def _read_release_torrent_metadata(cls, release: Release):
        with release.torrent_file.open("rb") as torrent_handle:
            return parse_torrent(torrent_handle.read())

    @classmethod
    def _normalize_webseed_upload_entries(cls, *, metadata, webseed_files, webseed_paths) -> dict[str, object]:
        if not webseed_files:
            return {}
        if len(webseed_files) != len(webseed_paths):
            raise BusinessException("分流文件与路径数量不一致，请重新选择后再试。")

        expected_entries: dict[str, int] = {}
        for item in getattr(metadata, "files", []) or []:
            normalized_path = cls._normalize_relative_path(item.path or "")
            if normalized_path:
                expected_entries[normalized_path] = int(item.size_bytes or 0)

        if not expected_entries:
            raise BusinessException("当前 torrent 没有可用于分流的文件清单。")

        if len(expected_entries) == 1 and len(webseed_files) == 1:
            expected_path = next(iter(expected_entries))
            upload_file = webseed_files[0]
            expected_size = expected_entries[expected_path]
            upload_size = int(getattr(upload_file, "size", 0) or 0)
            if expected_size and upload_size and expected_size != upload_size:
                raise BusinessException("上传的分流文件大小与 torrent 记录不一致。")
            return {expected_path: upload_file}

        normalized_entries: list[tuple[object, str]] = []
        for upload_file, raw_path in zip(webseed_files, webseed_paths):
            normalized_path = cls._normalize_relative_path(raw_path or getattr(upload_file, "name", ""))
            if not normalized_path:
                raise BusinessException("分流文件缺少相对路径，请重新选择文件或目录。")
            normalized_entries.append((upload_file, normalized_path))

        expected_paths = set(expected_entries)
        provided_entries = next(
            (
                candidate_entries
                for candidate_entries in cls._build_webseed_path_candidates(normalized_entries)
                if set(candidate_entries) == expected_paths
            ),
            None,
        )
        provided_paths = set(provided_entries or {})
        if expected_paths != provided_paths:
            missing_paths = sorted(expected_paths - provided_paths)
            extra_paths = sorted(provided_paths - expected_paths)
            details: list[str] = []
            if missing_paths:
                details.append(f"缺少：{', '.join(missing_paths[:3])}")
            if extra_paths:
                details.append(f"多余：{', '.join(extra_paths[:3])}")
            raise BusinessException(f"分流文件结构与 torrent 不匹配。{'；'.join(details)}")

        assert provided_entries is not None
        for relative_path, upload_file in provided_entries.items():
            expected_size = expected_entries[relative_path]
            upload_size = int(getattr(upload_file, "size", 0) or 0)
            if expected_size and upload_size and expected_size != upload_size:
                raise BusinessException(f"分流文件大小不匹配：{relative_path}")
        return provided_entries

        provided_entries: dict[str, object] = {}
        root_name = cls._normalize_relative_path(getattr(metadata, "name", "") or "")
        for upload_file, raw_path in zip(webseed_files, webseed_paths):
            normalized_path = cls._normalize_relative_path(raw_path or getattr(upload_file, "name", ""))
            if root_name and normalized_path.startswith(f"{root_name}/"):
                normalized_path = normalized_path[len(root_name) + 1 :]
            normalized_path = cls._normalize_relative_path(normalized_path)
            if not normalized_path:
                raise BusinessException("分流文件缺少相对路径，请重新选择文件或目录。")
            if normalized_path in provided_entries:
                raise BusinessException(f"检测到重复的分流文件路径：{normalized_path}")
            provided_entries[normalized_path] = upload_file

        expected_paths = set(expected_entries)
        provided_paths = set(provided_entries)
        if expected_paths != provided_paths:
            missing_paths = sorted(expected_paths - provided_paths)
            extra_paths = sorted(provided_paths - expected_paths)
            details: list[str] = []
            if missing_paths:
                details.append(f"缺少：{', '.join(missing_paths[:3])}")
            if extra_paths:
                details.append(f"多余：{', '.join(extra_paths[:3])}")
            raise BusinessException(f"分流文件结构与 torrent 不匹配。{'；'.join(details)}")

        for relative_path, upload_file in provided_entries.items():
            expected_size = expected_entries[relative_path]
            upload_size = int(getattr(upload_file, "size", 0) or 0)
            if expected_size and upload_size and expected_size != upload_size:
                raise BusinessException(f"分流文件大小不匹配：{relative_path}")
        return provided_entries

    @classmethod
    def _webseed_storage_relative_path(cls, *, metadata, relative_path: str) -> str:
        root_name = cls._normalize_relative_path(getattr(metadata, "name", "") or "") or "download"
        if len(getattr(metadata, "files", []) or []) == 1:
            return root_name
        return f"{root_name}/{relative_path}"

    @staticmethod
    def _clear_webseed_files(release: Release) -> None:
        existing_files = list(release.webseed_files.all())
        if not existing_files:
            return

        storage = ReleaseWebseedFile._meta.get_field("storage_file").storage
        stored_names = [item.storage_file.name for item in existing_files if item.storage_file and item.storage_file.name]
        release.webseed_files.all().delete()
        for stored_name in stored_names:
            storage.delete(stored_name)

    @classmethod
    def _replace_webseed_files(cls, *, release: Release, metadata, webseed_files, webseed_paths) -> None:
        upload_entries = cls._normalize_webseed_upload_entries(
            metadata=metadata,
            webseed_files=webseed_files,
            webseed_paths=webseed_paths,
        )
        cls._clear_webseed_files(release)
        if not upload_entries:
            return

        for relative_path, upload_file in upload_entries.items():
            storage_relative_path = cls._webseed_storage_relative_path(metadata=metadata, relative_path=relative_path)
            storage_name = f"{release.pk}/{storage_relative_path}"
            webseed_file = ReleaseWebseedFile(
                release=release,
                relative_path=relative_path,
                size_bytes=int(getattr(upload_file, "size", 0) or 0),
            )
            if hasattr(upload_file, "seek"):
                upload_file.seek(0)
            webseed_file.storage_file.save(storage_name, upload_file, save=False)
            webseed_file.save()

    @staticmethod
    def _get_default_category():
        category = Category.objects.filter(is_active=True).order_by("sort_order", "id").first()
        if category is None:
            raise BusinessException("当前没有可用分类，请先在后台创建并启用至少一个分类。")
        return category

    @staticmethod
    def _default_title_from_torrent_metadata(metadata) -> str | None:
        files = getattr(metadata, "files", None) or []
        info_name = (getattr(metadata, "name", None) or "").strip()

        if not files:
            if not info_name:
                return None
            return PurePosixPath(info_name).stem.strip() or None

        if len(files) == 1:
            path = (files[0].path or "").strip() or info_name
            if not path:
                return None
            stem = PurePosixPath(path).stem.strip()
            return stem or None

        paths = [(item.path or "").strip() for item in files if (item.path or "").strip()]
        if not paths:
            if not info_name:
                return None
            return PurePosixPath(info_name).stem.strip() or None

        any_nested = any("/" in path for path in paths)
        if any_nested:
            if not info_name:
                return PurePosixPath(paths[0]).stem.strip() or None
            return PurePosixPath(info_name).stem.strip() or None

        first_stem = PurePosixPath(paths[0]).stem.strip()
        if first_stem:
            return first_stem
        if info_name:
            return PurePosixPath(info_name).stem.strip() or None
        return None

    @staticmethod
    def _build_default_title(*, payload: dict, torrent_file, metadata) -> str:
        explicit_title = (payload.get("title") or "").strip()
        if explicit_title:
            return explicit_title[:255]

        from_meta = ReleaseService._default_title_from_torrent_metadata(metadata)
        if from_meta:
            return from_meta[:255]

        original_name = Path(getattr(torrent_file, "name", "upload.torrent")).stem.strip()
        if original_name:
            return original_name[:255]

        return f"资源 {metadata.infohash[:8]}"

    @classmethod
    @transaction.atomic
    def normalize_existing_release_torrent(cls, release: Release) -> Release:
        with release.torrent_file.open("rb") as torrent_handle:
            current_bytes = torrent_handle.read()

        normalized_torrent_bytes = TrackerService.normalize_uploaded_torrent(current_bytes)
        if normalized_torrent_bytes == current_bytes:
            return release

        metadata = parse_torrent(normalized_torrent_bytes)
        duplicated = Release.objects.exclude(pk=release.pk).filter(infohash=metadata.infohash).exists()
        if duplicated:
            raise BusinessException("规范化历史种子后产生了重复的 infohash，请手动处理该资源。")

        stored_torrent = ContentFile(normalized_torrent_bytes)
        stored_torrent.name = Path(release.torrent_file.name).name or f"release-{release.pk}.torrent"
        release.torrent_file = stored_torrent
        release.infohash = metadata.infohash
        release.size_bytes = metadata.size_bytes
        release.save(update_fields=["torrent_file", "infohash", "size_bytes", "updated_at"])
        release.files.all().delete()
        ReleaseFile.objects.bulk_create(
            [
                ReleaseFile(release=release, file_path=item.path, file_size=item.size_bytes)
                for item in metadata.files
            ]
        )
        return release

    @classmethod
    @transaction.atomic
    def create_release(cls, *, actor, payload: dict):
        payload = dict(payload)
        tags = payload.pop("tags", [])
        torrent_file = payload.pop("torrent_file")
        webseed_files = payload.pop("webseed_files", [])
        webseed_paths = payload.pop("webseed_paths", [])
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
        if webseed_files:
            cls._replace_webseed_files(
                release=release,
                metadata=metadata,
                webseed_files=webseed_files,
                webseed_paths=webseed_paths,
            )
        AuditService.log(
            actor,
            "发布资源",
            "资源",
            release.title,
            detail="上传 torrent 并写入文件列表。",
            payload={"release_id": release.id},
        )
        TrackerSyncService.schedule_release_sync(release=release)
        return release

    @classmethod
    @transaction.atomic
    def update_release(cls, *, actor, release: Release, payload: dict):
        previous_infohash = release.infohash
        previous_status = release.status

        tags = payload.pop("tags", None)
        torrent_file = payload.pop("torrent_file", None)
        webseed_files = payload.pop("webseed_files", None)
        webseed_paths = payload.pop("webseed_paths", [])
        clear_webseed_files = bool(payload.pop("clear_webseed_files", False))
        metadata = None
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
        if clear_webseed_files:
            cls._clear_webseed_files(release)
        elif webseed_files is not None:
            active_metadata = metadata or cls._read_release_torrent_metadata(release)
            cls._replace_webseed_files(
                release=release,
                metadata=active_metadata,
                webseed_files=webseed_files,
                webseed_paths=webseed_paths,
            )
        elif torrent_file:
            cls._clear_webseed_files(release)
        AuditService.log(
            actor,
            "编辑资源",
            "资源",
            release.title,
            detail="资源元数据已更新。",
            payload={"release_id": release.id},
        )
        TrackerSyncService.schedule_release_sync(
            release=release,
            previous_infohash=previous_infohash,
            previous_status=previous_status,
        )
        return release

    @classmethod
    @transaction.atomic
    def set_visibility(cls, *, actor, release: Release, status: str):
        previous_infohash = release.infohash
        previous_status = release.status

        release.status = status
        update_fields = ["status", "updated_at"]
        if status == ReleaseStatus.PUBLISHED and not release.published_at:
            release.published_at = timezone.now()
        update_fields.append("published_at")
        release.save(update_fields=update_fields)
        AuditService.log(
            actor,
            "恢复资源" if status == ReleaseStatus.PUBLISHED else "隐藏资源",
            "资源",
            release.title,
            detail=f"资源状态切换为 {status}。",
            payload={"release_id": release.id},
        )
        TrackerSyncService.schedule_release_sync(
            release=release,
            previous_infohash=previous_infohash,
            previous_status=previous_status,
        )
        return release
