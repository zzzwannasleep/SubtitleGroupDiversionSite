import json
import os
import tempfile
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.common.throttles import LoginRateThrottle
from apps.common.torrent import bdecode, bencode
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        existing_tables = set(connection.introspection.table_names())
        with connection.cursor() as cursor:
            if XbtUserMirror._meta.db_table not in existing_tables:
                cursor.execute(
                    """
                    CREATE TABLE xbt_users (
                        uid INTEGER PRIMARY KEY,
                        torrent_pass VARCHAR(32) NOT NULL UNIQUE,
                        can_leech BOOLEAN NOT NULL DEFAULT 1,
                        downloaded BIGINT NOT NULL DEFAULT 0,
                        uploaded BIGINT NOT NULL DEFAULT 0,
                        completed INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                existing_tables.add(XbtUserMirror._meta.db_table)
            if XbtFileMirror._meta.db_table not in existing_tables:
                cursor.execute(
                    """
                    CREATE TABLE xbt_torrents (
                        tid INTEGER PRIMARY KEY AUTOINCREMENT,
                        info_hash BLOB NOT NULL UNIQUE,
                        leechers INTEGER NOT NULL DEFAULT 0,
                        seeders INTEGER NOT NULL DEFAULT 0,
                        completed INTEGER NOT NULL DEFAULT 0,
                        flags INTEGER NOT NULL DEFAULT 0,
                        mtime INTEGER NOT NULL DEFAULT 0,
                        ctime INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                existing_tables.add(XbtFileMirror._meta.db_table)

    def setUp(self):
        self.client = APIClient()
        XbtFileMirror.objects.all().delete()
        XbtUserMirror.objects.all().delete()
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
        torrent = bdecode(response.content)
        self.assertEqual(
            torrent[b"announce"].decode("utf-8"),
            f"http://localhost:8000/{self.user.passkey}/announce",
        )

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

    def test_admin_can_update_user_profile_fields(self):
        self.client.force_login(self.admin)
        response = self.client.patch(
            f"/api/admin/users/{self.user.id}/",
            {
                "displayName": "更新后的用户",
                "email": "updated-user@example.com",
                "role": "uploader",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "更新后的用户")
        self.assertEqual(self.user.email, "updated-user@example.com")
        self.assertEqual(self.user.role, "uploader")
        self.assertTrue(AuditLog.objects.filter(action="更新用户", target_name=self.user.username).exists())

    def test_admin_can_disable_and_enable_user_with_explicit_routes(self):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            disable = self.client.post(f"/api/admin/users/{self.user.id}/disable/")
        self.assertEqual(disable.status_code, 200, disable.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.status, "disabled")
        self.assertFalse(XbtUserMirror.objects.get(uid=self.user.id).can_leech)

        with self.captureOnCommitCallbacks(execute=True):
            enable = self.client.post(f"/api/admin/users/{self.user.id}/enable/")
        self.assertEqual(enable.status_code, 200, enable.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.status, "active")
        self.assertTrue(XbtUserMirror.objects.get(uid=self.user.id).can_leech)

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

    def test_user_can_get_own_theme(self):
        self.user.theme_mode = "dark"
        self.user.theme_custom_css = "body { color: red; }"
        self.user.save(update_fields=["theme_mode", "theme_custom_css"])

        self.client.force_login(self.user)
        response = self.client.get("/api/me/theme/")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(
            response.json()["data"],
            {
                "mode": "dark",
                "customCss": "body { color: red; }",
            },
        )

    def test_user_can_update_own_theme(self):
        self.client.force_login(self.user)
        response = self.client.put(
            "/api/me/theme/",
            {
                "mode": "light",
                "customCss": ":root { --primary: 16 185 129; }",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.theme_mode, "light")
        self.assertEqual(self.user.theme_custom_css, ":root { --primary: 16 185 129; }")

    def test_openapi_schema_validates_and_describes_core_contracts(self):
        fd, schema_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            call_command(
                "spectacular",
                format="openapi-json",
                file=schema_path,
                validate=True,
                fail_on_warn=True,
                stdout=StringIO(),
                stderr=StringIO(),
            )

            with open(schema_path, "r", encoding="utf-8") as handle:
                schema = json.load(handle)
        finally:
            if os.path.exists(schema_path):
                os.remove(schema_path)

        self.assertIn("/api/releases/", schema["paths"])
        self.assertIn("/api/admin/tracker-sync/full/", schema["paths"])
        self.assertIn("sessionCookieAuth", schema["components"]["securitySchemes"])
        self.assertIn("multipart/form-data", schema["paths"]["/api/releases/"]["post"]["requestBody"]["content"])
