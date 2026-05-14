from pathlib import Path, PurePosixPath

from django.conf import settings
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
    WEBSEED_RESERVED_PREFIXES = {"release-webseeds", "site", "torrent_templates"}

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
        result = "/".join(parts)
        max_length = ReleaseWebseedFile._meta.get_field("relative_path").max_length or 700
        if len(result) > max_length:
            raise BusinessException(f"分流文件路径过长，不能超过 {max_length} 个字符。")
        return result

    @classmethod
    def _ensure_managed_webseed_storage_path_allowed(cls, value: str) -> str:
        normalized = cls._normalize_relative_path(value)
        if not normalized:
            raise BusinessException("分流文件路径不能为空。")

        first_segment = PurePosixPath(normalized).parts[0]
        if first_segment in cls.WEBSEED_RESERVED_PREFIXES:
            raise BusinessException(f"分流文件不能写入站点内部目录：{first_segment}")
        return normalized

    @classmethod
    def _webseed_library_root(cls) -> Path:
        return Path(getattr(settings, "WEBSEED_LIBRARY_ROOT", settings.MEDIA_ROOT))

    @classmethod
    def _webseed_library_shares_media_root(cls) -> bool:
        return cls._webseed_library_root().resolve(strict=False) == Path(settings.MEDIA_ROOT).resolve(strict=False)

    @classmethod
    def _ensure_webseed_library_path_allowed(cls, value: str) -> str:
        normalized = cls._normalize_relative_path(value)
        if not normalized:
            raise BusinessException("分流文件路径不能为空。")

        if cls._webseed_library_shares_media_root():
            first_segment = PurePosixPath(normalized).parts[0]
            if first_segment in cls.WEBSEED_RESERVED_PREFIXES:
                raise BusinessException(f"映射目录不能引用站点内部目录：{first_segment}")
        return normalized

    @classmethod
    def _build_expected_webseed_entries(cls, metadata) -> dict[str, int]:
        expected_entries: dict[str, int] = {}
        for item in getattr(metadata, "files", []) or []:
            normalized_path = cls._normalize_relative_path(item.path or "")
            if normalized_path:
                expected_entries[normalized_path] = int(item.size_bytes or 0)

        if not expected_entries:
            raise BusinessException("当前 torrent 没有可用于分流的文件清单。")
        return expected_entries

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
            for entry, normalized_path in normalized_entries:
                candidate_path = cls._strip_leading_segments(normalized_path, strip_count)
                if not candidate_path or candidate_path in candidate_entries:
                    valid = False
                    break
                candidate_entries[candidate_path] = entry
            if valid:
                candidates.append(candidate_entries)
        return candidates

    @classmethod
    def _build_matching_webseed_entries(
        cls,
        *,
        normalized_entries: list[tuple[object, str]],
        expected_paths: set[str],
    ) -> dict[str, object]:
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
            detail_message = f"（{'；'.join(details)}）" if details else ""
            raise BusinessException(f"分流文件结构与 torrent 不匹配。{detail_message}")

        return provided_entries or {}

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

        expected_entries = cls._build_expected_webseed_entries(metadata)

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

        provided_entries = cls._build_matching_webseed_entries(
            normalized_entries=normalized_entries,
            expected_paths=set(expected_entries),
        )
        for relative_path, upload_file in provided_entries.items():
            expected_size = expected_entries[relative_path]
            upload_size = int(getattr(upload_file, "size", 0) or 0)
            if expected_size and upload_size and expected_size != upload_size:
                raise BusinessException(f"分流文件大小不匹配：{relative_path}")
        return provided_entries

    @classmethod
    def _list_existing_webseed_source_entries(cls, webseed_root_path: str) -> list[dict[str, object]]:
        normalized_root = cls._ensure_webseed_library_path_allowed(webseed_root_path)
        library_root = cls._webseed_library_root()
        absolute_root = library_root.joinpath(*PurePosixPath(normalized_root).parts)
        if not absolute_root.exists():
            raise BusinessException("所选映射目录中的文件或文件夹不存在。")

        if absolute_root.is_file():
            return [{"path": normalized_root, "size_bytes": int(absolute_root.stat().st_size)}]

        source_entries: list[dict[str, object]] = []
        for absolute_path in sorted(absolute_root.rglob("*")):
            if not absolute_path.is_file():
                continue
            relative_path = absolute_path.relative_to(library_root).as_posix()
            source_entries.append({"path": relative_path, "size_bytes": int(absolute_path.stat().st_size)})

        if not source_entries:
            raise BusinessException("所选目录内没有可用文件。")
        return source_entries

    @classmethod
    def _build_expected_webseed_source_path(cls, *, metadata, relative_path: str) -> str:
        root_name = cls._normalize_relative_path(getattr(metadata, "name", "") or "") or "download"
        if len(getattr(metadata, "files", []) or []) == 1:
            return root_name
        return cls._normalize_relative_path(f"{root_name}/{relative_path}")

    @classmethod
    def _build_uploaded_webseed_storage_path(cls, *, metadata, relative_path: str) -> str:
        return cls._ensure_managed_webseed_storage_path_allowed(
            cls._build_expected_webseed_source_path(metadata=metadata, relative_path=relative_path)
        )

    @classmethod
    def _normalize_existing_webseed_entries(cls, *, metadata, webseed_root_path: str) -> dict[str, dict[str, object]]:
        if not webseed_root_path:
            return {}

        expected_entries = cls._build_expected_webseed_entries(metadata)
        expected_source_entries = {
            cls._build_expected_webseed_source_path(metadata=metadata, relative_path=relative_path): {
                "relative_path": relative_path,
                "size_bytes": size_bytes,
            }
            for relative_path, size_bytes in expected_entries.items()
        }
        source_entries = cls._list_existing_webseed_source_entries(webseed_root_path)
        normalized_entries = [(entry, str(entry["path"])) for entry in source_entries]
        provided_entries = cls._build_matching_webseed_entries(
            normalized_entries=normalized_entries,
            expected_paths=set(expected_source_entries),
        )

        resolved_entries: dict[str, dict[str, object]] = {}
        for source_path, source_entry in provided_entries.items():
            source_size = int(source_entry["size_bytes"] or 0)
            expected_size = expected_source_entries[source_path]["size_bytes"]
            if expected_size and source_size and expected_size != source_size:
                raise BusinessException(f"分流文件大小不匹配：{source_path}")
            relative_path = str(expected_source_entries[source_path]["relative_path"])
            resolved_entries[relative_path] = {
                "source_path": str(source_entry["path"]),
                "size_bytes": source_size,
            }
        return resolved_entries

    @classmethod
    def _resolve_existing_webseed_library_entries(
        cls,
        *,
        metadata,
        webseed_root_path: str,
    ) -> dict[str, dict[str, object]]:
        if not webseed_root_path:
            return {}

        expected_entries = cls._build_expected_webseed_entries(metadata)
        expected_source_entries = {
            cls._build_expected_webseed_source_path(metadata=metadata, relative_path=relative_path): {
                "relative_path": relative_path,
                "size_bytes": size_bytes,
            }
            for relative_path, size_bytes in expected_entries.items()
        }
        source_entries = cls._list_existing_webseed_source_entries(webseed_root_path)
        normalized_entries = [(entry, str(entry["path"])) for entry in source_entries]
        provided_entries = cls._build_matching_webseed_entries(
            normalized_entries=normalized_entries,
            expected_paths=set(expected_source_entries),
        )

        resolved_entries: dict[str, dict[str, object]] = {}
        for source_path, source_entry in provided_entries.items():
            source_size = int(source_entry["size_bytes"] or 0)
            expected_size = int(expected_source_entries[source_path]["size_bytes"] or 0)
            if expected_size and source_size and expected_size != source_size:
                raise BusinessException(f"分流文件大小不匹配：{source_path}")
            relative_path = str(expected_source_entries[source_path]["relative_path"])
            resolved_entries[relative_path] = {
                "source_path": str(source_entry["path"]),
                "size_bytes": source_size,
            }
        return resolved_entries

    @staticmethod
    def _clear_webseed_files(release: Release) -> None:
        release.webseed_files.all().delete()

    @classmethod
    def _save_uploaded_webseed_file(cls, *, upload_file, storage_name: str) -> str:
        storage = ReleaseWebseedFile._meta.get_field("storage_file").storage
        if storage.exists(storage_name):
            raise BusinessException(f"映射目录中已存在同名文件：{storage_name}")
        if hasattr(upload_file, "seek"):
            upload_file.seek(0)
        saved_name = storage.save(storage_name, upload_file)
        if saved_name != storage_name:
            storage.delete(saved_name)
            raise BusinessException(f"分流文件保存路径冲突：{storage_name}")
        return saved_name

    @classmethod
    def _replace_webseed_files(cls, *, release: Release, metadata, webseed_files, webseed_paths, webseed_root_path="") -> None:
        if webseed_files and webseed_root_path:
            raise BusinessException("请选择一种分流来源：本地上传或服务器目录。")

        upload_entries = cls._normalize_webseed_upload_entries(
            metadata=metadata,
            webseed_files=webseed_files,
            webseed_paths=webseed_paths,
        )
        existing_entries = cls._resolve_existing_webseed_library_entries(
            metadata=metadata,
            webseed_root_path=webseed_root_path,
        )
        cls._clear_webseed_files(release)
        if not upload_entries and not existing_entries:
            return

        for relative_path, upload_file in upload_entries.items():
            storage_relative_path = cls._build_uploaded_webseed_storage_path(
                metadata=metadata,
                relative_path=relative_path,
            )
            storage_name = cls._save_uploaded_webseed_file(upload_file=upload_file, storage_name=storage_relative_path)
            ReleaseWebseedFile.objects.create(
                release=release,
                relative_path=relative_path,
                size_bytes=int(getattr(upload_file, "size", 0) or 0),
                storage_file=storage_name,
            )

        for relative_path, source_entry in existing_entries.items():
            ReleaseWebseedFile.objects.create(
                release=release,
                relative_path=relative_path,
                size_bytes=int(source_entry["size_bytes"] or 0),
                storage_file=str(source_entry["source_path"]),
            )

    @classmethod
    def _build_webseed_directory_parent_path(cls, path: str) -> str | None:
        normalized = cls._normalize_relative_path(path)
        if not normalized:
            return None
        parent = PurePosixPath(normalized).parent.as_posix()
        return "" if parent == "." else parent

    @classmethod
    def list_webseed_directory(cls, path: str = "") -> dict[str, object]:
        normalized_path = cls._normalize_relative_path(path)
        if normalized_path:
            normalized_path = cls._ensure_webseed_library_path_allowed(normalized_path)

        library_root = cls._webseed_library_root()
        current_dir = library_root if not normalized_path else library_root.joinpath(*PurePosixPath(normalized_path).parts)
        if not current_dir.exists():
            raise BusinessException("所选映射目录不存在。")
        if not current_dir.is_dir():
            raise BusinessException("只能浏览映射目录中的文件夹。")

        entries: list[dict[str, object]] = []
        for child in sorted(current_dir.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            relative_path = child.relative_to(library_root).as_posix()
            if not normalized_path and cls._webseed_library_shares_media_root() and child.name in cls.WEBSEED_RESERVED_PREFIXES:
                continue
            entries.append(
                {
                    "name": child.name,
                    "path": relative_path,
                    "kind": "directory" if child.is_dir() else "file",
                    "sizeBytes": None if child.is_dir() else int(child.stat().st_size),
                }
            )

        return {
            "currentPath": normalized_path,
            "parentPath": cls._build_webseed_directory_parent_path(normalized_path),
            "entries": entries,
        }

    @staticmethod
    def build_webseed_library_preview(*, request, torrent_file, webseed_root_path: str) -> dict[str, object]:
        normalized_root_path = ReleaseService._ensure_webseed_library_path_allowed(webseed_root_path)
        torrent_bytes = torrent_file.read()
        if hasattr(torrent_file, "seek"):
            torrent_file.seek(0)
        metadata = parse_torrent(TrackerService.normalize_uploaded_torrent(torrent_bytes))
        resolved_entries = ReleaseService._resolve_existing_webseed_library_entries(
            metadata=metadata,
            webseed_root_path=normalized_root_path,
        )

        from apps.downloads.services import DownloadService

        preview_entries = [
            {
                "relativePath": relative_path,
                "sourcePath": str(source_entry["source_path"]),
                "sizeBytes": int(source_entry["size_bytes"] or 0),
                "directUrl": DownloadService.build_webseed_file_url(
                    stored_path=str(source_entry["source_path"]),
                    request=request,
                ),
            }
            for relative_path, source_entry in sorted(resolved_entries.items())
        ]
        root_url = DownloadService.build_webseed_root_url_for_paths(
            stored_paths=[str(source_entry["source_path"]) for source_entry in resolved_entries.values()],
            relative_paths=list(resolved_entries),
            request=request,
        )

        return {
            "selectionPath": normalized_root_path,
            "torrentName": getattr(metadata, "name", "") or "",
            "rootUrl": root_url,
            "httpSeedUrl": DownloadService.build_httpseed_url_for_infohash(
                infohash=getattr(metadata, "infohash", ""),
                request=request,
            ),
            "files": preview_entries,
        }

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
        webseed_root_path = payload.pop("webseed_root_path", "")
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
        if webseed_files or webseed_root_path:
            cls._replace_webseed_files(
                release=release,
                metadata=metadata,
                webseed_files=webseed_files,
                webseed_paths=webseed_paths,
                webseed_root_path=webseed_root_path,
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
        webseed_root_path = payload.pop("webseed_root_path", "")
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
        elif webseed_files is not None or webseed_root_path:
            active_metadata = metadata or cls._read_release_torrent_metadata(release)
            cls._replace_webseed_files(
                release=release,
                metadata=active_metadata,
                webseed_files=webseed_files or [],
                webseed_paths=webseed_paths,
                webseed_root_path=webseed_root_path,
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
