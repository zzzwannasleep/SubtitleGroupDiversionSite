from urllib.parse import quote, urlencode
from xml.sax.saxutils import escape

from django.conf import settings

from apps.announcements.models import SiteSetting
from apps.releases.models import Release
from apps.tracker.services import TrackerService


class RssService:
    @staticmethod
    def get_rss_base_url():
        setting = SiteSetting.get_current()
        base_path = setting.rss_base_path or "/rss"
        if base_path.startswith("http://") or base_path.startswith("https://"):
            return base_path.rstrip("/")
        return f"{settings.SITE_BASE_URL.rstrip('/')}/{base_path.lstrip('/')}"

    @classmethod
    def build_overview(cls, user=None):
        recent_titles = list(
            Release.objects.filter(status="published").order_by("-published_at", "-id").values_list("title", flat=True)[:4]
        )

        personal_feed = ""
        if cls.can_build_personal_feed(user):
            try:
                passkey = TrackerService.ensure_user_key(user)
                personal_feed = cls.build_personal_feed_url(passkey)
            except Exception:
                personal_feed = ""

        return {
            "personalFeed": personal_feed,
            "recentReleaseTitles": recent_titles,
        }

    @classmethod
    def can_build_personal_feed(cls, user) -> bool:
        return bool(
            user
            and getattr(user, "is_authenticated", False)
            and getattr(user, "status", None) == "active"
            and TrackerService.is_enabled()
            and TrackerService.auth_mode() == "per_user"
        )

    @classmethod
    def build_personal_feed_url(cls, passkey: str) -> str:
        return f"{cls.get_rss_base_url()}/passkey/{quote(passkey, safe='')}/all"

    @staticmethod
    def resolve_personal_feed_user(passkey: str):
        return TrackerService.resolve_active_user_by_passkey(passkey)

    @staticmethod
    def build_feed(title: str, releases, *, passkey: str = ""):
        base = settings.SITE_BASE_URL.rstrip("/")
        items = []
        query_suffix = f"?{urlencode({'passkey': passkey})}" if passkey else ""

        for release in releases[:50]:
            download_link = f"{base}/api/releases/{release.id}/download/{query_suffix}"
            items.append(
                "<item>"
                f"<title>{escape(release.title)}</title>"
                f"<description>{escape(release.subtitle or release.description or release.title)}</description>"
                f"<link>{escape(download_link)}</link>"
                f"<guid>{escape(release.infohash if not passkey else f'{release.infohash}:{passkey}')}</guid>"
                f"<pubDate>{release.published_at:%a, %d %b %Y %H:%M:%S %z}</pubDate>"
                "</item>"
            )
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            "<rss version=\"2.0\">"
            "<channel>"
            f"<title>{escape(title)}</title>"
            f"<link>{escape(base)}</link>"
            f"<description>{escape(title)}</description>"
            + "".join(items)
            + "</channel></rss>"
        )
