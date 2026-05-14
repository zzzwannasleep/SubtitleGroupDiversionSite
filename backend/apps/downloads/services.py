from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, quote, urljoin

from django.conf import settings
from django.db.models import F
from rest_framework.exceptions import PermissionDenied

from apps.common.exceptions import BusinessException
from apps.common.torrent import parse_torrent, read_torrent
from apps.downloads.models import DownloadLog
from apps.tracker.services import TrackerService
from apps.users.models import UserStatus


class DownloadService:
    @staticmethod
    def _webseed_library_root() -> Path:
        return Path(getattr(settings, "WEBSEED_LIBRARY_ROOT", settings.MEDIA_ROOT))

    @staticmethod
    def resolve_user(request):
        user = request.user
        if getattr(user, "is_authenticated", False):
            if getattr(user, "status", None) != UserStatus.ACTIVE:
                raise PermissionDenied("当前账号已被禁用。")
            return user

        passkey = request.GET.get("passkey")
        if passkey:
            tracked_user = TrackerService.resolve_active_user_by_passkey(passkey)
            if tracked_user is None:
                raise PermissionDenied("RSS passkey 无效或账号已被禁用。")
            return tracked_user

        if TrackerService.require_authenticated_downloads():
            raise PermissionDenied("Private Tracker 已启用，请先登录后再下载种子。")
        return None

    @classmethod
    def build_download_torrent(cls, *, user, release, request):
        if release.status != "published":
            raise PermissionDenied("当前资源不可下载。")

        with release.torrent_file.open("rb") as torrent_handle:
            torrent_bytes = torrent_handle.read()

        webseed_root_url = cls._build_webseed_root_url(release=release, request=request)
        httpseed_url = cls.build_httpseed_url(release=release, request=request)
        if TrackerService.is_enabled() or webseed_root_url or httpseed_url:
            announce_url = TrackerService.get_announce_url_for_user(user) if TrackerService.is_enabled() else None
            torrent_bytes = TrackerService.rewrite_download_torrent(
                torrent_bytes=torrent_bytes,
                announce_url=announce_url,
                webseed_urls=[webseed_root_url] if webseed_root_url else None,
                httpseed_urls=[httpseed_url] if httpseed_url else None,
            )

        DownloadLog.objects.create(
            user=user,
            release=release,
            ip_address=cls._extract_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        type(release).objects.filter(pk=release.pk).update(download_count=F("download_count") + 1)

        filename = Path(release.torrent_file.name).name or f"release-{release.pk}.torrent"
        if not filename.lower().endswith(".torrent"):
            filename = f"{filename}.torrent"
        return torrent_bytes, filename

    @staticmethod
    def _normalize_public_path(value: str) -> str:
        normalized = (value or "/").strip() or "/"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if not normalized.endswith("/"):
            normalized = f"{normalized}/"
        return normalized

    @classmethod
    def _build_public_base_url(cls, *, source_kind: str, request) -> str:
        if source_kind == "library":
            public_base = (getattr(settings, "WEBSEED_LIBRARY_PUBLIC_URL", "") or "").strip().rstrip("/")
            if public_base:
                return f"{public_base}/"
            return request.build_absolute_uri(cls._normalize_public_path(settings.WEBSEED_LIBRARY_URL_PATH))
        return request.build_absolute_uri(cls._normalize_public_path(settings.MEDIA_URL))

    @classmethod
    def _join_public_url(cls, *, base_url: str, relative_path: str = "", trailing_slash: bool = False) -> str:
        encoded_path = quote((relative_path or "").strip("/"), safe="/")
        if trailing_slash and encoded_path:
            encoded_path = f"{encoded_path}/"
        if trailing_slash and not encoded_path:
            return base_url.rstrip("/") + "/"
        if not encoded_path:
            return base_url
        return urljoin(base_url, encoded_path)

    @staticmethod
    def _resolve_webseed_source_kind(*, stored_path: str) -> str:
        candidate = str(stored_path or "").strip()
        if not candidate:
            return "library"

        managed_path = Path(settings.MEDIA_ROOT).joinpath(*PurePosixPath(candidate).parts)
        library_path = DownloadService._webseed_library_root().joinpath(*PurePosixPath(candidate).parts)

        library_exists = library_path.exists()
        if library_exists:
            return "library"
        if managed_path.exists():
            return "managed"
        return "library"

    @classmethod
    def build_webseed_file_url(cls, *, stored_path: str, request) -> str:
        source_kind = cls._resolve_webseed_source_kind(stored_path=stored_path)
        base_url = cls._build_public_base_url(source_kind=source_kind, request=request)
        return cls._join_public_url(base_url=base_url, relative_path=stored_path)

    @classmethod
    def build_webseed_root_url_for_paths(cls, *, stored_paths: list[str], relative_paths: list[str], request) -> str | None:
        if not stored_paths or not relative_paths:
            return None

        first_stored_path = str(stored_paths[0] or "").strip()
        first_relative_path = str(relative_paths[0] or "").strip()
        stored_parts = list(PurePosixPath(first_stored_path).parts)
        relative_parts = list(PurePosixPath(first_relative_path).parts)
        strip_count = len(relative_parts) + (1 if len(stored_paths) > 1 else 0)
        root_parts = stored_parts[:-strip_count] if strip_count > 0 else stored_parts
        root_suffix = "/".join(root_parts).strip("/")
        source_kind = cls._resolve_webseed_source_kind(stored_path=first_stored_path)
        base_url = cls._build_public_base_url(source_kind=source_kind, request=request)
        return cls._join_public_url(base_url=base_url, relative_path=root_suffix, trailing_slash=True)

    @staticmethod
    def build_httpseed_url_for_infohash(*, infohash: str, request) -> str:
        return request.build_absolute_uri(f"/api/httpseed/{str(infohash or '').strip().lower()}/")

    @staticmethod
    def build_httpseed_url(*, release, request) -> str | None:
        if not release.webseed_files.exists():
            return None
        return DownloadService.build_httpseed_url_for_infohash(infohash=release.infohash, request=request)

    @classmethod
    def _build_webseed_root_url(cls, *, release, request) -> str | None:
        webseed_files = list(release.webseed_files.all())
        if not webseed_files:
            return None
        return cls.build_webseed_root_url_for_paths(
            stored_paths=[str(item.storage_file.name) for item in webseed_files],
            relative_paths=[str(item.relative_path) for item in webseed_files],
            request=request,
        )

    @staticmethod
    def _parse_httpseed_query(request) -> tuple[bytes, int, list[tuple[int, int]]]:
        query_bytes = (request.META.get("QUERY_STRING") or "").encode("ascii", "ignore")
        params = parse_qs(query_bytes, keep_blank_values=True)

        info_hash = params.get(b"info_hash", [b""])[0]
        piece_raw = params.get(b"piece", [b""])[0]
        if len(info_hash) != 20 or not piece_raw:
            raise BusinessException("HTTP seed 请求缺少必要参数。")

        try:
            piece_index = int(piece_raw.decode("ascii"))
        except ValueError as exc:
            raise BusinessException("HTTP seed 的 piece 参数无效。") from exc

        ranges_raw = params.get(b"ranges", [b""])[0]
        parsed_ranges: list[tuple[int, int]] = []
        if ranges_raw:
            try:
                for item in ranges_raw.decode("ascii").split(","):
                    start_text, end_text = item.split("-", 1)
                    start = int(start_text)
                    end = int(end_text)
                    parsed_ranges.append((start, end))
            except ValueError as exc:
                raise BusinessException("HTTP seed 的 ranges 参数无效。") from exc

        return info_hash, piece_index, parsed_ranges

    @staticmethod
    def _resolve_local_webseed_path(stored_path: str) -> Path:
        candidate = str(stored_path or "").strip()
        if not candidate:
            raise BusinessException("分流文件路径为空。")

        managed_path = Path(settings.MEDIA_ROOT).joinpath(*PurePosixPath(candidate).parts)
        library_path = DownloadService._webseed_library_root().joinpath(*PurePosixPath(candidate).parts)
        if library_path.exists():
            return library_path
        if managed_path.exists():
            return managed_path
        return library_path

    @classmethod
    def _build_ordered_httpseed_sources(cls, *, release) -> tuple[list[tuple[Path, int]], int]:
        with release.torrent_file.open("rb") as torrent_handle:
            torrent_bytes = torrent_handle.read()

        torrent = read_torrent(torrent_bytes)
        metadata = parse_torrent(torrent_bytes)
        webseed_map = {str(item.relative_path): str(item.storage_file.name) for item in release.webseed_files.all()}
        ordered_sources: list[tuple[Path, int]] = []

        for file_entry in metadata.files:
            stored_path = webseed_map.get(str(file_entry.path))
            if not stored_path:
                raise BusinessException(f"缺少分流文件映射：{file_entry.path}")
            ordered_sources.append((cls._resolve_local_webseed_path(stored_path), int(file_entry.size_bytes or 0)))

        piece_size = int(getattr(torrent, "piece_size", 0) or 0)
        if piece_size <= 0:
            raise BusinessException("torrent 缺少有效的 piece length。")
        return ordered_sources, piece_size

    @staticmethod
    def _normalize_piece_ranges(*, piece_length: int, ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if piece_length <= 0:
            raise BusinessException("HTTP seed 请求的 piece 超出范围。")
        if not ranges:
            return [(0, piece_length - 1)]

        normalized: list[tuple[int, int]] = []
        for start, end in ranges:
            if start < 0 or end < start or end >= piece_length:
                raise BusinessException("HTTP seed 的 ranges 超出 piece 范围。")
            normalized.append((start, end))
        return normalized

    @staticmethod
    def _read_global_range(*, ordered_sources: list[tuple[Path, int]], start: int, end_exclusive: int) -> bytes:
        if end_exclusive <= start:
            return b""

        cursor = 0
        chunks: list[bytes] = []
        for absolute_path, file_size in ordered_sources:
            file_start = cursor
            file_end = cursor + file_size
            overlap_start = max(start, file_start)
            overlap_end = min(end_exclusive, file_end)
            if overlap_start < overlap_end:
                if not absolute_path.exists():
                    raise BusinessException(f"分流文件不存在：{absolute_path.as_posix()}")
                with absolute_path.open("rb") as file_handle:
                    file_handle.seek(overlap_start - file_start)
                    chunks.append(file_handle.read(overlap_end - overlap_start))
            cursor = file_end
            if cursor >= end_exclusive:
                break
        return b"".join(chunks)

    @classmethod
    def build_httpseed_response_body(cls, *, release, request) -> bytes:
        if release.status != "published":
            raise PermissionDenied("当前资源不可下载。")
        if not release.webseed_files.exists():
            raise BusinessException("当前资源未配置 webseed。")

        info_hash_bytes, piece_index, ranges = cls._parse_httpseed_query(request)
        if info_hash_bytes.hex() != str(release.infohash or "").lower():
            raise BusinessException("HTTP seed 的 info_hash 不匹配。")

        ordered_sources, piece_size = cls._build_ordered_httpseed_sources(release=release)
        total_size = sum(file_size for _, file_size in ordered_sources)
        piece_start = piece_index * piece_size
        if piece_index < 0 or piece_start >= total_size:
            raise BusinessException("HTTP seed 请求的 piece 超出范围。")

        piece_end = min(total_size, piece_start + piece_size)
        piece_length = piece_end - piece_start
        normalized_ranges = cls._normalize_piece_ranges(piece_length=piece_length, ranges=ranges)

        chunks: list[bytes] = []
        for start, end in normalized_ranges:
            chunks.append(
                cls._read_global_range(
                    ordered_sources=ordered_sources,
                    start=piece_start + start,
                    end_exclusive=piece_start + end + 1,
                )
            )
        return b"".join(chunks)

    @staticmethod
    def _extract_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
