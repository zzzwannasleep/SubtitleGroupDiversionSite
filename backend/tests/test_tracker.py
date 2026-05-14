import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import quote_from_bytes

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from torf import _flatbencode as flatbencode

from apps.releases.models import Category, Release, Tag
from apps.tracker.models import TrackerPeerSnapshot, TrackerTorrentSync
from apps.tracker.services import TorrustAuthKey, TorrustClient, TrackerApiStats, TrackerScrapeStats
from apps.users.models import User


def build_torrent_bytes(*, private: bool = True) -> bytes:
    return flatbencode.encode(
        {
            b"announce": b"https://example.com/announce",
            b"info": {
                b"name": b"Example.S01E01.mkv",
                b"piece length": 262144,
                b"pieces": b"01234567890123456789",
                b"length": 1024,
                b"private": 1 if private else 0,
            },
        }
    )


class TrackerApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_media_dir = tempfile.mkdtemp(prefix="subtitle-group-tracker-tests-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media_dir)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        try:
            super().tearDownClass()
        finally:
            cls._media_override.disable()
            shutil.rmtree(cls._temp_media_dir, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="动画", slug="anime", sort_order=1, is_active=True)
        self.tag = Tag.objects.create(name="1080p", slug="1080p")
        self.admin = User.objects.create_user(
            username="admin",
            password="Admin12345!",
            display_name="Admin User",
            role="admin",
            status="active",
            email="admin@example.com",
        )
        self.uploader = User.objects.create_user(
            username="uploader",
            password="Uploader12345!",
            display_name="Uploader User",
            role="uploader",
            status="active",
            email="uploader@example.com",
        )
        self.user = User.objects.create_user(
            username="user",
            password="User12345!",
            display_name="Regular User",
            role="user",
            status="active",
            email="user@example.com",
        )

    def create_release(self, *, status: str = "published", execute_on_commit: bool = False, torrent_bytes: bytes | None = None):
        self.client.force_login(self.uploader)
        torrent = SimpleUploadedFile(
            "example.torrent",
            torrent_bytes or build_torrent_bytes(),
            content_type="application/x-bittorrent",
        )
        payload = {
            "title": "测试资源",
            "subtitle": "WEB-DL 1080p",
            "description": "资源说明",
            "categorySlug": self.category.slug,
            "tagSlugs": [self.tag.slug],
            "status": status,
            "torrentFile": torrent,
        }
        if execute_on_commit:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/api/releases/", payload, format="multipart")
        else:
            response = self.client.post("/api/releases/", payload, format="multipart")
        self.assertEqual(response.status_code, 201, response.json())
        self.client.logout()
        return Release.objects.get(pk=response.json()["data"]["id"])

    @staticmethod
    def make_tracker_http_response(body: bytes, *, status_code: int = 200, content_type: str = "text/plain"):
        response = MagicMock()
        entered = response.__enter__.return_value
        entered.status = status_code
        entered.read.return_value = body
        entered.headers.get_content_type.return_value = content_type
        return response

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
        TRACKER_AUTH_MODE="per_user",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch(
        "apps.tracker.services.TorrustClient.create_auth_key",
        return_value=TorrustAuthKey("user-passkey", datetime(2026, 5, 12, 8, 0, tzinfo=UTC)),
    )
    def test_me_tracker_endpoint_returns_urls_and_passkey(self, _create_auth_key):
        self.client.force_login(self.user)
        response = self.client.get("/api/me/tracker/")
        self.assertEqual(response.status_code, 200, response.json())

        self.user.refresh_from_db()
        self.assertEqual(
            {**response.json()["data"], "keyValidUntil": None},
            {
                "enabled": True,
                "authMode": "per_user",
                "announceUrl": "https://tracker.example.com/announce/user-passkey",
                "scrapeUrl": "https://tracker.example.com/scrape/user-passkey",
                "passkey": "user-passkey",
                "keyValidUntil": None,
                "requireAuthDownloads": True,
                "forcePrivateTorrents": True,
            },
        )
        self.assertEqual(response.json()["data"]["keyValidUntil"], "2026-05-12T08:00:00Z")
        self.assertEqual(self.user.tracker_passkey, "user-passkey")

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
        TRACKER_AUTH_URL_STYLE="prefix",
        TRACKER_AUTH_MODE="per_user",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch(
        "apps.tracker.services.TorrustClient.create_auth_key",
        return_value=TorrustAuthKey("user-passkey", datetime(2026, 5, 12, 8, 0, tzinfo=UTC)),
    )
    def test_me_tracker_endpoint_supports_prefix_auth_url_style(self, _create_auth_key):
        self.client.force_login(self.user)
        response = self.client.get("/api/me/tracker/")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["data"]["announceUrl"], "https://tracker.example.com/user-passkey/announce")
        self.assertEqual(response.json()["data"]["scrapeUrl"], "https://tracker.example.com/user-passkey/scrape")

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="http://tracker:7070/scrape",
        TRACKER_AUTH_MODE="per_user",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch(
        "apps.tracker.services.TorrustClient.create_auth_key",
        return_value=TorrustAuthKey("user-passkey", datetime(2026, 5, 12, 8, 0, tzinfo=UTC)),
    )
    def test_me_tracker_endpoint_derives_public_scrape_url_when_internal_scrape_url_is_private(self, _create_auth_key):
        self.client.force_login(self.user)
        response = self.client.get("/api/me/tracker/")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["data"]["scrapeUrl"], "https://tracker.example.com/scrape/user-passkey")

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
        TRACKER_AUTH_MODE="shared",
        TORRUST_SHARED_AUTH_KEY="shared-key",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch("apps.tracker.services.TorrustClient.whitelist_infohash")
    @patch(
        "apps.tracker.services.TorrustClient.get_stats",
        return_value=TrackerApiStats(
            torrents=12,
            seeders=34,
            leechers=5,
            completed=20,
            announces_handled=99,
            scrapes_handled=18,
        ),
    )
    def test_admin_tracker_overview_returns_local_and_remote_metrics(self, _get_stats, _whitelist_infohash):
        published_release = self.create_release(execute_on_commit=True)
        draft_release = self.create_release(
            status="draft",
            execute_on_commit=True,
            torrent_bytes=build_torrent_bytes().replace(b"Example.S01E01.mkv", b"Example.S01E02.mkv"),
        )
        TrackerTorrentSync.objects.filter(release=draft_release).update(last_error="sync failed")

        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/tracker/overview/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertTrue(data["enabled"])
        self.assertTrue(data["trackerReachable"])
        self.assertEqual(data["announceUrl"], "https://tracker.example.com/announce")
        self.assertEqual(data["scrapeUrl"], "https://tracker.example.com/scrape")
        self.assertEqual(data["authMode"], "shared")
        self.assertEqual(data["publishedReleaseCount"], 1)
        self.assertEqual(data["releaseSyncCount"], 2)
        self.assertEqual(data["whitelistedReleaseCount"], 1)
        self.assertEqual(data["syncErrorCount"], 1)
        self.assertEqual(
            data["trackerStats"],
            {
                "torrents": 12,
                "seeders": 34,
                "leechers": 5,
                "completed": 20,
                "announcesHandled": 99,
                "scrapesHandled": 18,
            },
        )

        sync = TrackerTorrentSync.objects.get(release=published_release)
        self.assertTrue(sync.is_whitelisted)

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com:7070/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com:7070/scrape",
        TRACKER_AUTH_MODE="shared",
        TORRUST_SHARED_AUTH_KEY="shared-key",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch(
        "apps.tracker.services.TorrustClient.get_stats",
        return_value=TrackerApiStats(
            torrents=0,
            seeders=0,
            leechers=0,
            completed=0,
            announces_handled=0,
            scrapes_handled=0,
        ),
    )
    def test_admin_tracker_overview_warns_on_https_7070_announce_url(self, _get_stats):
        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/tracker/overview/")
        self.assertEqual(response.status_code, 200, response.json())

        tracker_message = response.json()["data"]["trackerMessage"]
        self.assertIn("https://...:7070", tracker_message)
        self.assertIn("qBittorrent", tracker_message)

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
        TRACKER_AUTH_MODE="per_user",
        TRACKER_REQUIRE_AUTH_DOWNLOADS=True,
        TRACKER_FORCE_PRIVATE_TORRENTS=True,
        TORRUST_API_URL="https://tracker.example.com",
        TORRUST_API_TOKEN="tracker-token",
    )
    @patch("apps.tracker.services.TorrustClient.whitelist_infohash")
    @patch(
        "apps.tracker.services.TorrustClient.create_auth_key",
        return_value=TorrustAuthKey("uploader-passkey", timezone.now() + timedelta(days=30)),
    )
    @patch(
        "apps.tracker.services.TorrustClient.scrape_infohash",
        return_value=TrackerScrapeStats(seeders=5, leechers=2, completed=11),
    )
    def test_admin_tracker_sync_endpoint_updates_release_scrape_stats(
        self,
        scrape_infohash,
        _create_auth_key,
        _whitelist_infohash,
    ):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/admin/tracker/sync/",
            {"syncScrape": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(
            response.json()["data"],
            {
                "usersProcessed": 0,
                "usersFailed": 0,
                "releasesProcessed": 0,
                "releasesFailed": 0,
                "scrapesProcessed": 1,
                "scrapesFailed": 0,
                "errors": [],
            },
        )

        release.refresh_from_db()
        sync = TrackerTorrentSync.objects.get(release=release)
        self.assertEqual(release.active_peers, 7)
        self.assertEqual(release.completion_count, 11)
        self.assertEqual(sync.last_scrape_seeders, 5)
        self.assertEqual(sync.last_scrape_leechers, 2)
        self.assertEqual(sync.last_scrape_completed, 11)
        scrape_infohash.assert_called_once_with(infohash=release.infohash, auth_key="uploader-passkey")

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
    )
    @patch("apps.tracker.services.urlopen")
    def test_torrust_client_scrape_infohash_uses_auth_path_and_binary_query(self, mocked_urlopen):
        infohash = "4df4010a4af5f6082705df0ea5c79d0fceba9f10"
        infohash_bytes = bytes.fromhex(infohash)
        response_body = flatbencode.encode(
            {
                b"files": {
                    infohash_bytes: {
                        b"complete": 4,
                        b"incomplete": 3,
                        b"downloaded": 12,
                    }
                }
            }
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = response_body
        mocked_urlopen.return_value = response

        client = TorrustClient(base_url="https://tracker.example.com", token="tracker-token", timeout=5)
        stats = client.scrape_infohash(infohash=infohash, auth_key="user-key")

        self.assertEqual(stats, TrackerScrapeStats(seeders=4, leechers=3, completed=12))
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://tracker.example.com/scrape/user-key?info_hash="))
        self.assertIn("%F4", request.full_url.upper())

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="http://tracker:7070/scrape",
    )
    @patch("apps.tracker.services.urlopen")
    def test_torrust_client_scrape_infohash_prefers_internal_scrape_url_when_configured(self, mocked_urlopen):
        infohash = "4df4010a4af5f6082705df0ea5c79d0fceba9f10"
        infohash_bytes = bytes.fromhex(infohash)
        response_body = flatbencode.encode(
            {
                b"files": {
                    infohash_bytes: {
                        b"complete": 4,
                        b"incomplete": 3,
                        b"downloaded": 12,
                    }
                }
            }
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = response_body
        mocked_urlopen.return_value = response

        client = TorrustClient(base_url="https://tracker.example.com", token="tracker-token", timeout=5)
        stats = client.scrape_infohash(infohash=infohash, auth_key="user-key")

        self.assertEqual(stats, TrackerScrapeStats(seeders=4, leechers=3, completed=12))
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.startswith("http://tracker:7070/scrape/user-key?info_hash="))

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://tracker.example.com/announce",
        TRACKER_SCRAPE_URL="https://tracker.example.com/scrape",
        TRACKER_AUTH_URL_STYLE="prefix",
    )
    @patch("apps.tracker.services.urlopen")
    def test_torrust_client_scrape_infohash_supports_prefix_auth_url_style(self, mocked_urlopen):
        infohash = "4df4010a4af5f6082705df0ea5c79d0fceba9f10"
        infohash_bytes = bytes.fromhex(infohash)
        response_body = flatbencode.encode(
            {
                b"files": {
                    infohash_bytes: {
                        b"complete": 4,
                        b"incomplete": 3,
                        b"downloaded": 12,
                    }
                }
            }
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = response_body
        mocked_urlopen.return_value = response

        client = TorrustClient(base_url="https://tracker.example.com", token="tracker-token", timeout=5)
        stats = client.scrape_infohash(infohash=infohash, auth_key="user-key")

        self.assertEqual(stats, TrackerScrapeStats(seeders=4, leechers=3, completed=12))
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.startswith("https://tracker.example.com/user-key/scrape?info_hash="))

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://site.example.com/tracker/announce",
        TRACKER_INTERNAL_ANNOUNCE_URL="http://tracker:7070/announce",
        TRACKER_SCRAPE_URL="http://tracker:7070/scrape",
        TRACKER_PUBLIC_SCRAPE_URL="https://site.example.com/tracker/scrape",
        TRACKER_AUTH_MODE="per_user",
    )
    @patch("apps.tracker.proxy.urlopen")
    def test_tracker_announce_proxy_updates_user_stats_on_each_announce(self, mocked_urlopen):
        release = self.create_release()
        self.user.tracker_passkey = "user-passkey"
        self.user.tracker_key_valid_until = timezone.now() + timedelta(days=30)
        self.user.save(update_fields=["tracker_passkey", "tracker_key_valid_until"])

        mocked_urlopen.return_value = self.make_tracker_http_response(
            flatbencode.encode({b"interval": 120, b"complete": 1, b"incomplete": 0, b"peers": b""})
        )
        info_hash = quote_from_bytes(bytes.fromhex(release.infohash), safe="")
        peer_id = quote_from_bytes(b"-UT0001-123456789012", safe="")

        started = self.client.get(
            f"/tracker/announce/user-passkey?info_hash={info_hash}&peer_id={peer_id}&port=6881&uploaded=0&downloaded=0&left=1024&event=started"
        )
        self.assertEqual(started.status_code, 200)

        completed = self.client.get(
            f"/tracker/announce/user-passkey?info_hash={info_hash}&peer_id={peer_id}&port=6881&uploaded=0&downloaded=1024&left=0&event=completed"
        )
        self.assertEqual(completed.status_code, 200)

        announced = self.client.get(
            f"/tracker/announce/user-passkey?info_hash={info_hash}&peer_id={peer_id}&port=6881&uploaded=2048&downloaded=1024&left=0"
        )
        self.assertEqual(announced.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.uploaded_bytes, 2048)
        self.assertEqual(self.user.downloaded_bytes, 1024)
        self.assertEqual(self.user.seeding_count, 1)
        self.assertEqual(self.user.seeding_size_bytes, release.size_bytes)

        stopped = self.client.get(
            f"/tracker/announce/user-passkey?info_hash={info_hash}&peer_id={peer_id}&port=6881&uploaded=4096&downloaded=1024&left=0&event=stopped"
        )
        self.assertEqual(stopped.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.uploaded_bytes, 4096)
        self.assertEqual(self.user.downloaded_bytes, 1024)
        self.assertEqual(self.user.seeding_count, 0)
        self.assertEqual(self.user.seeding_size_bytes, 0)
        self.assertFalse(TrackerPeerSnapshot.objects.filter(user=self.user).exists())

        forwarded_request = mocked_urlopen.call_args.args[0]
        self.assertTrue(forwarded_request.full_url.startswith("http://tracker:7070/announce/user-passkey?info_hash="))
        self.assertEqual(forwarded_request.headers["X-forwarded-for"], "127.0.0.1")

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://site.example.com/tracker/announce",
        TRACKER_INTERNAL_ANNOUNCE_URL="http://tracker:7070/announce",
        TRACKER_SCRAPE_URL="http://tracker:7070/scrape",
        TRACKER_PUBLIC_SCRAPE_URL="https://site.example.com/tracker/scrape",
        TRACKER_AUTH_MODE="per_user",
    )
    @patch("apps.tracker.proxy.urlopen")
    def test_tracker_scrape_proxy_forwards_request(self, mocked_urlopen):
        self.user.tracker_passkey = "user-passkey"
        self.user.tracker_key_valid_until = timezone.now() + timedelta(days=30)
        self.user.save(update_fields=["tracker_passkey", "tracker_key_valid_until"])

        infohash = "4df4010a4af5f6082705df0ea5c79d0fceba9f10"
        response_body = flatbencode.encode(
            {
                b"files": {
                    bytes.fromhex(infohash): {
                        b"complete": 4,
                        b"incomplete": 3,
                        b"downloaded": 12,
                    }
                }
            }
        )
        mocked_urlopen.return_value = self.make_tracker_http_response(response_body)

        response = self.client.get(f"/tracker/scrape/user-passkey?info_hash={quote_from_bytes(bytes.fromhex(infohash), safe='')}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, response_body)

        forwarded_request = mocked_urlopen.call_args.args[0]
        self.assertTrue(forwarded_request.full_url.startswith("http://tracker:7070/scrape/user-passkey?info_hash="))

    @override_settings(
        TRACKER_ENABLED=True,
        TRACKER_ANNOUNCE_URL="https://site.example.com/tracker/announce",
        TRACKER_INTERNAL_ANNOUNCE_URL="http://tracker:7070/announce",
        TRACKER_AUTH_MODE="per_user",
    )
    @patch("apps.tracker.proxy.urlopen")
    def test_tracker_announce_proxy_rejects_disabled_or_unknown_key(self, mocked_urlopen):
        response = self.client.get("/tracker/announce/unknown-key?uploaded=0&downloaded=0&left=0")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"failure reason", response.content)
        mocked_urlopen.assert_not_called()
