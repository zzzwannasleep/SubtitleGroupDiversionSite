from xml.sax.saxutils import escape

from django.conf import settings

from apps.announcements.models import SiteSetting
from apps.releases.models import Release


class RssService:
    @staticmethod
    def get_rss_base_url():
        setting = SiteSetting.get_current()
        base_path = setting.rss_base_path or "/rss"
        if base_path.startswith("http://") or base_path.startswith("https://"):
            return base_path.rstrip("/")
        return f"{settings.SITE_BASE_URL.rstrip('/')}/{base_path.lstrip('/')}"

    @classmethod
    def build_overview(cls):
        base = cls.get_rss_base_url()
        recent_titles = list(
            Release.objects.filter(status="published").order_by("-published_at", "-id").values_list("title", flat=True)[:4]
        )
        return {
            "generalFeed": f"{base}/all",
            "recentReleaseTitles": recent_titles,
        }

    @staticmethod
    def build_feed(title: str, releases):
        base = settings.SITE_BASE_URL.rstrip("/")
        items = []
        for release in releases[:50]:
            download_link = f"{base}/api/releases/{release.id}/download/"
            items.append(
                "<item>"
                f"<title>{escape(release.title)}</title>"
                f"<description>{escape(release.subtitle or release.description or release.title)}</description>"
                f"<link>{escape(download_link)}</link>"
                f"<guid>{escape(release.infohash)}</guid>"
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
