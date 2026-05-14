from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import unquote_to_bytes
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from torf import _flatbencode as flatbencode

from apps.releases.models import Release
from apps.tracker.models import TrackerPeerSnapshot
from apps.tracker.services import TrackerService
from apps.users.models import User


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TrackerProxyResult:
    status_code: int
    body: bytes
    content_type: str


@dataclass(slots=True)
class TrackerAnnouncePayload:
    infohash: str
    peer_id: str
    uploaded_bytes: int
    downloaded_bytes: int
    left_bytes: int
    event: str
    port: int | None


class TrackerProxyService:
    @staticmethod
    def build_failure_response(message: str) -> TrackerProxyResult:
        body = flatbencode.encode({b"failure reason": str(message).encode("utf-8", errors="ignore")})
        return TrackerProxyResult(status_code=200, body=body, content_type="text/plain")

    @classmethod
    def proxy_announce(cls, *, auth_key: str, query_string: str, remote_ip: str = "", user_agent: str = "") -> TrackerProxyResult:
        tracked_user = TrackerService.resolve_active_user_by_passkey(auth_key)
        if TrackerService.auth_mode() == "per_user" and tracked_user is None:
            return cls.build_failure_response("Invalid or disabled tracker key.")

        upstream = TrackerService.build_internal_announce_url(auth_key)
        result = cls._forward_tracker_request(
            upstream_url=upstream,
            query_string=query_string,
            remote_ip=remote_ip,
            user_agent=user_agent,
        )
        if tracked_user is not None and result.status_code == 200 and not cls._has_failure_reason(result.body):
            try:
                cls._record_successful_announce(
                    user_id=tracked_user.id,
                    query_string=query_string,
                    remote_ip=remote_ip,
                )
            except Exception:  # pragma: no cover - defensive logging path
                logger.warning("Failed to sync user stats from tracker announce for user=%s", tracked_user.id, exc_info=True)
        return result

    @classmethod
    def proxy_scrape(cls, *, auth_key: str, query_string: str, remote_ip: str = "", user_agent: str = "") -> TrackerProxyResult:
        if TrackerService.auth_mode() == "per_user" and TrackerService.resolve_active_user_by_passkey(auth_key) is None:
            return cls.build_failure_response("Invalid or disabled tracker key.")

        upstream = TrackerService.build_internal_scrape_url(auth_key)
        return cls._forward_tracker_request(
            upstream_url=upstream,
            query_string=query_string,
            remote_ip=remote_ip,
            user_agent=user_agent,
        )

    @classmethod
    def _forward_tracker_request(
        cls,
        *,
        upstream_url: str,
        query_string: str,
        remote_ip: str = "",
        user_agent: str = "",
    ) -> TrackerProxyResult:
        request_url = upstream_url if not query_string else f"{upstream_url}?{query_string}"
        request = Request(request_url, method="GET")
        request.add_header("Accept", "text/plain, application/octet-stream, */*")
        if user_agent:
            request.add_header("User-Agent", user_agent)
        if remote_ip:
            request.add_header("X-Forwarded-For", remote_ip)
            request.add_header("X-Real-IP", remote_ip)

        timeout = float(getattr(settings, "TORRUST_API_TIMEOUT_SECONDS", 5) or 5)
        try:
            with urlopen(request, timeout=timeout) as response:
                status_code = int(getattr(response, "status", 200) or 200)
                headers = getattr(response, "headers", None)
                content_type = (
                    headers.get_content_type()
                    if headers is not None and hasattr(headers, "get_content_type")
                    else "text/plain"
                )
                return TrackerProxyResult(status_code=status_code, body=response.read(), content_type=content_type)
        except HTTPError as exc:
            headers = getattr(exc, "headers", None)
            content_type = (
                headers.get_content_type()
                if headers is not None and hasattr(headers, "get_content_type")
                else "text/plain"
            )
            return TrackerProxyResult(status_code=exc.code, body=exc.read(), content_type=content_type)
        except URLError:
            return cls.build_failure_response("Unable to reach the upstream tracker.")

    @classmethod
    def _record_successful_announce(cls, *, user_id: int, query_string: str, remote_ip: str = "") -> None:
        payload = cls._parse_announce_payload(query_string)
        if payload is None:
            return

        with transaction.atomic():
            cls._delete_stale_snapshots(user_id=user_id)
            user = User.objects.select_for_update().get(pk=user_id)
            release = Release.objects.filter(infohash=payload.infohash).only("id", "size_bytes").first()
            snapshot = (
                TrackerPeerSnapshot.objects.select_for_update()
                .filter(user=user, infohash=payload.infohash, peer_id=payload.peer_id)
                .first()
            )

            uploaded_delta = 0
            downloaded_delta = 0
            if snapshot is not None:
                uploaded_delta = cls._compute_counter_delta(payload.uploaded_bytes, snapshot.uploaded_bytes)
                downloaded_delta = cls._compute_counter_delta(payload.downloaded_bytes, snapshot.downloaded_bytes)

            user.uploaded_bytes += uploaded_delta
            user.downloaded_bytes += downloaded_delta

            if payload.event == "stopped":
                if snapshot is not None:
                    snapshot.delete()
            else:
                torrent_size_bytes = int(getattr(release, "size_bytes", 0) or 0)
                if snapshot is None:
                    snapshot = TrackerPeerSnapshot.objects.create(
                        user=user,
                        release=release,
                        infohash=payload.infohash,
                        peer_id=payload.peer_id,
                        torrent_size_bytes=torrent_size_bytes,
                        uploaded_bytes=payload.uploaded_bytes,
                        downloaded_bytes=payload.downloaded_bytes,
                        left_bytes=payload.left_bytes,
                        ip_address=remote_ip or None,
                        port=payload.port,
                        last_event=payload.event,
                    )
                else:
                    snapshot.release = release
                    snapshot.torrent_size_bytes = torrent_size_bytes
                    snapshot.uploaded_bytes = payload.uploaded_bytes
                    snapshot.downloaded_bytes = payload.downloaded_bytes
                    snapshot.left_bytes = payload.left_bytes
                    snapshot.ip_address = remote_ip or snapshot.ip_address
                    snapshot.port = payload.port
                    snapshot.last_event = payload.event
                    snapshot.save(
                        update_fields=[
                            "release",
                            "torrent_size_bytes",
                            "uploaded_bytes",
                            "downloaded_bytes",
                            "left_bytes",
                            "ip_address",
                            "port",
                            "last_event",
                            "last_announced_at",
                        ]
                    )

            seeding_count, seeding_size_bytes = cls._calculate_seeding_metrics(user_id=user.id)
            user.seeding_count = seeding_count
            user.seeding_size_bytes = seeding_size_bytes
            user.save(update_fields=["uploaded_bytes", "downloaded_bytes", "seeding_count", "seeding_size_bytes"])

    @staticmethod
    def refresh_user_seeding_metrics(*, user_id: int) -> None:
        with transaction.atomic():
            TrackerProxyService._delete_stale_snapshots(user_id=user_id)
            user = User.objects.select_for_update().get(pk=user_id)
            seeding_count, seeding_size_bytes = TrackerProxyService._calculate_seeding_metrics(user_id=user_id)
            user.seeding_count = seeding_count
            user.seeding_size_bytes = seeding_size_bytes
            user.save(update_fields=["seeding_count", "seeding_size_bytes"])

    @staticmethod
    def _delete_stale_snapshots(*, user_id: int | None = None) -> None:
        stale_seconds = int(getattr(settings, "TRACKER_PEER_SNAPSHOT_STALE_SECONDS", 900) or 900)
        cutoff = timezone.now() - timedelta(seconds=stale_seconds)
        queryset = TrackerPeerSnapshot.objects.filter(last_announced_at__lt=cutoff)
        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)
        queryset.delete()

    @staticmethod
    def _calculate_seeding_metrics(*, user_id: int) -> tuple[int, int]:
        rows = TrackerPeerSnapshot.objects.filter(user_id=user_id, left_bytes=0).values("infohash", "torrent_size_bytes")
        unique_sizes: dict[str, int] = {}
        for row in rows:
            unique_sizes[str(row["infohash"])] = int(row["torrent_size_bytes"] or 0)
        return len(unique_sizes), sum(unique_sizes.values())

    @staticmethod
    def _compute_counter_delta(current_value: int, previous_value: int) -> int:
        if current_value < previous_value:
            return 0
        return current_value - previous_value

    @classmethod
    def _parse_announce_payload(cls, query_string: str) -> TrackerAnnouncePayload | None:
        params = cls._parse_query_string(query_string)
        infohash_bytes = params.get("info_hash")
        peer_id_bytes = params.get("peer_id")
        if not infohash_bytes or not peer_id_bytes:
            return None

        return TrackerAnnouncePayload(
            infohash=infohash_bytes.hex(),
            peer_id=peer_id_bytes.hex(),
            uploaded_bytes=cls._parse_int(params.get("uploaded")),
            downloaded_bytes=cls._parse_int(params.get("downloaded")),
            left_bytes=cls._parse_int(params.get("left")),
            event=(params.get("event") or b"").decode("utf-8", errors="ignore").strip().lower(),
            port=cls._parse_optional_int(params.get("port")),
        )

    @staticmethod
    def _parse_query_string(query_string: str) -> dict[str, bytes]:
        parsed: dict[str, bytes] = {}
        if not query_string:
            return parsed

        for chunk in query_string.split("&"):
            if not chunk:
                continue
            raw_key, _, raw_value = chunk.partition("=")
            key = unquote_to_bytes(raw_key).decode("ascii", errors="ignore")
            if key and key not in parsed:
                parsed[key] = unquote_to_bytes(raw_value)
        return parsed

    @staticmethod
    def _parse_int(value: bytes | None) -> int:
        if not value:
            return 0
        try:
            return max(int(value.decode("ascii", errors="ignore") or "0"), 0)
        except ValueError:
            return 0

    @classmethod
    def _parse_optional_int(cls, value: bytes | None) -> int | None:
        if value in (None, b""):
            return None
        return cls._parse_int(value)

    @staticmethod
    def _has_failure_reason(body: bytes) -> bool:
        try:
            payload = flatbencode.decode(body)
        except Exception:
            return True
        if not isinstance(payload, dict):
            return True
        return bool(payload.get(b"failure reason") or payload.get("failure reason"))
