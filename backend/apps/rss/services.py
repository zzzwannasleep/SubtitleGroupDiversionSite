from xml.sax.saxutils import escape

from django.conf import settings

from apps.announcements.models import SiteSetting
from apps.releases.models import Category, Release, Tag
from apps.users.models import User, UserStatus


class RssService:
    @staticmethod
    def resolve_access_user(token_or_passkey: str):
        return User.objects.filter(passkey=token_or_passkey, status=UserStatus.ACTIVE).first()

    @classmethod
    def resolve_passkey_user(cls, passkey: str):
        return cls.resolve_access_user(passkey)

    @staticmethod
    def get_rss_base_url():
        setting = SiteSetting.get_current()
        base_path = setting.rss_base_path or "/rss"
        if base_path.startswith("http://") or base_path.startswith("https://"):
            return base_path.rstrip("/")
        return f"{settings.SITE_BASE_URL.rstrip('/')}/{base_path.lstrip('/')}"

    @classmethod
    def build_overview(cls, user):
        base = cls.get_rss_base_url()
        recent_titles = list(
            Release.objects.filter(status="published").order_by("-published_at", "-id").values_list("title", flat=True)[:4]
        )
        return {
            "generalFeed": f"{base}/all?passkey={user.passkey}",
            "categoryFeeds": [
                {"label": category.name, "url": f"{base}/category/{category.slug}?passkey={user.passkey}"}
                for category in Category.objects.filter(is_active=True).order_by("sort_order", "id")
            ],
            "tagFeeds": [
                {"label": tag.name, "url": f"{base}/tag/{tag.slug}?passkey={user.passkey}"}
                for tag in Tag.objects.order_by("name", "id")[:5]
            ],
            "recentReleaseTitles": recent_titles,
        }

    @staticmethod
    def build_feed(title: str, releases, passkey: str):
        base = settings.SITE_BASE_URL.rstrip("/")
        items = []
        for release in releases[:50]:
            download_link = f"{base}/api/releases/{release.id}/download/?passkey={passkey}"
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
