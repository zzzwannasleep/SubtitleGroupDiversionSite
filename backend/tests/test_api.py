from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.common.throttles import LoginRateThrottle
from apps.common.torrent import bencode
from apps.releases.models import Category, Release, Tag
from apps.tracker_sync.services import TrackerSyncService
from apps.tracker_sync.models import XbtFileMirror, XbtUserMirror
from apps.users.models import User


def build_torrent_bytes(*, private: bool = True) -> bytes:
    info = {
        b"name": b"Example.S01E01.mkv",
        b"piece length": 262144,
        b"pieces": b"01234567890123456789",
        b"length": 1024,
        b"private": 1 if private else 0,
    }
    return bencode({b"announce": b"https://tracker.example/announce", b"info": info})


@override_settings(MEDIA_ROOT="test-media")
class ApiFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="动画", slug="anime", sort_order=1, is_active=True)
        self.tag = Tag.objects.create(name="1080p", slug="1080p")
        self.admin = User.objects.create_user(
            username="admin",
            password="Admin12345!",
            display_name="管理员",
            role="admin",
            status="active",
            email="admin@example.com",
        )
        self.uploader = User.objects.create_user(
            username="uploader",
            password="Uploader12345!",
            display_name="上传者",
            role="uploader",
            status="active",
            email="uploader@example.com",
        )
        self.user = User.objects.create_user(
            username="user",
            password="User12345!",
            display_name="普通用户",
            role="user",
            status="active",
            email="user@example.com",
        )

    def create_release(self, *, status: str = "published", execute_on_commit: bool = False):
        self.client.force_login(self.uploader)
        torrent = SimpleUploadedFile("example.torrent", build_torrent_bytes(), content_type="application/x-bittorrent")
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

    def test_login_and_fetch_me(self):
        response = self.client.post("/api/auth/login/", {"username": "admin", "password": "Admin12345!"}, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200, me.json())
        self.assertEqual(me.json()["data"]["username"], "admin")

    def test_login_throttle_returns_unified_error(self):
        original_rates = LoginRateThrottle.THROTTLE_RATES
        LoginRateThrottle.THROTTLE_RATES = {**original_rates, "login": "2/min"}
        self.addCleanup(setattr, LoginRateThrottle, "THROTTLE_RATES", original_rates)
        self.addCleanup(cache.clear)
        cache.clear()

        payload = {"username": "admin", "password": "wrong-password"}
        first = self.client.post("/api/auth/login/", payload, format="json")
        second = self.client.post("/api/auth/login/", payload, format="json")
        third = self.client.post("/api/auth/login/", payload, format="json")

        self.assertEqual(first.status_code, 403, first.json())
        self.assertEqual(second.status_code, 403, second.json())
        self.assertEqual(third.status_code, 429, third.json())
        self.assertEqual(
            third.json(),
            {
                "success": False,
                "code": "throttled",
                "message": "请求过于频繁，请稍后再试。",
                "retryAfter": third.json()["retryAfter"],
            },
        )
        self.assertGreaterEqual(third.json()["retryAfter"], 0)

    def test_user_cannot_create_release(self):
        self.client.force_login(self.user)
        torrent = SimpleUploadedFile("example.torrent", build_torrent_bytes(), content_type="application/x-bittorrent")
        response = self.client.post(
            "/api/releases/",
            {
                "title": "无权限资源",
                "subtitle": "test",
                "description": "test",
                "categorySlug": self.category.slug,
                "tagSlugs": [self.tag.slug],
                "status": "published",
                "torrentFile": torrent,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 403, response.json())

    def test_uploader_can_create_release_and_download_personalized_torrent(self):
        release = self.create_release()
        self.client.force_login(self.user)
        response = self.client.get(f"/api/releases/{release.id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user.passkey.encode(), response.content)

    def test_rss_feed_uses_passkey_download_link(self):
        release = self.create_release()
        response = self.client.get(f"/rss/all?passkey={self.user.passkey}")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn(release.title, body)
        self.assertIn(self.user.passkey, body)

    def test_disabled_user_cannot_download_with_passkey(self):
        release = self.create_release()
        self.user.status = "disabled"
        self.user.save(update_fields=["status"])
        client = APIClient()
        response = client.get(f"/api/releases/{release.id}/download/?passkey={self.user.passkey}")
        self.assertEqual(response.status_code, 403, response.json())

    def test_draft_release_only_syncs_to_xbt_after_publish(self):
        release = self.create_release(status="draft", execute_on_commit=True)
        info_hash = bytes.fromhex(release.infohash)
        self.assertFalse(XbtFileMirror.objects.filter(info_hash=info_hash).exists())

        self.client.force_login(self.uploader)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/releases/{release.id}/",
                {"status": "published"},
                format="json",
            )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(XbtFileMirror.objects.filter(info_hash=info_hash, flags=0).exists())

    def test_hidden_release_marks_xbt_whitelist_record_deleted(self):
        release = self.create_release(execute_on_commit=True)
        info_hash = bytes.fromhex(release.infohash)
        self.assertTrue(XbtFileMirror.objects.filter(info_hash=info_hash, flags=0).exists())

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/api/releases/{release.id}/visibility/",
                {"status": "hidden"},
                format="json",
            )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(XbtFileMirror.objects.get(info_hash=info_hash).flags, 1)

    def test_reset_passkey_updates_xbt_user_mirror(self):
        self.client.force_login(self.user)
        old_passkey = self.user.passkey
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/me/reset-passkey/")
        self.assertEqual(response.status_code, 200, response.json())

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.passkey, old_passkey)
        self.assertEqual(XbtUserMirror.objects.get(uid=self.user.id).torrent_pass, self.user.passkey)

    def test_invalid_torrent_returns_unified_business_error(self):
        self.client.force_login(self.uploader)
        torrent = SimpleUploadedFile("broken.torrent", b"not-a-valid-torrent", content_type="application/x-bittorrent")
        response = self.client.post(
            "/api/releases/",
            {
                "title": "坏种子",
                "subtitle": "WEB-DL 1080p",
                "description": "资源说明",
                "categorySlug": self.category.slug,
                "tagSlugs": [self.tag.slug],
                "status": "published",
                "torrentFile": torrent,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "code": "business_error",
                "message": "无效的 torrent 文件。",
            },
        )

    def test_duplicate_username_returns_unified_validation_error(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/admin/users/",
            {
                "username": self.user.username,
                "displayName": "重复用户名用户",
                "email": "duplicate@example.com",
                "role": "user",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["code"], "validation_error")
        self.assertEqual(response.json()["message"], "参数校验失败。")
        self.assertEqual(response.json()["errors"], {"username": ["该用户名已存在。"]})

    def test_request_logging_redacts_passkey(self):
        self.create_release()
        with self.assertLogs("apps.request", level="INFO") as captured:
            response = self.client.get(f"/rss/all?passkey={self.user.passkey}")
        self.assertEqual(response.status_code, 200)

        combined = "\n".join(captured.output)
        self.assertIn("passkey=%2A%2A%2A", combined)
        self.assertIn("actor=passkey:user", combined)
        self.assertNotIn(self.user.passkey, combined)

    def test_admin_user_filters_match_role_and_status(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/users/?role=uploader&status=active")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["username"], "uploader")
        self.assertIsInstance(data[0]["lastLoginAt"], str)
        self.assertTrue(data[0]["lastLoginAt"])

    def test_my_releases_returns_safe_published_at_for_draft_release(self):
        release = self.create_release(status="draft")
        self.client.force_login(self.uploader)
        response = self.client.get("/api/me/releases/")
        self.assertEqual(response.status_code, 200, response.json())

        returned = next(item for item in response.json()["data"] if item["id"] == release.id)
        self.assertIsInstance(returned["publishedAt"], str)
        self.assertTrue(returned["publishedAt"])

    def test_admin_category_save_writes_audit_log(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/admin/categories/",
            {"name": "纪录片", "slug": "documentary"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(
            AuditLog.objects.filter(action="创建分类", target_type="分类", target_name="纪录片").exists()
        )

    def test_admin_user_detail_includes_tracker_sync_snapshot(self):
        TrackerSyncService.sync_user(self.user)

        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/users/{self.user.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["trackerSync"]["status"], "success")
        self.assertEqual(data["xbtUser"]["state"], "enabled")
        self.assertEqual(data["xbtUser"]["canLeech"], True)

    def test_release_detail_for_owner_includes_xbt_snapshot(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.uploader)
        response = self.client.get(f"/api/releases/{release.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["trackerSync"]["status"], "success")
        self.assertEqual(data["xbtFile"]["state"], "whitelisted")
        self.assertIsNotNone(data["xbtFile"]["updatedAt"])
