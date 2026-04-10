import json
import os
import tempfile
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from torf import Torrent, _flatbencode as flatbencode

from apps.announcements.models import SiteSetting
from apps.audit.models import AuditLog
from apps.common.throttles import LoginRateThrottle
from apps.releases.models import Category, Release, Tag
from apps.tracker_sync.models import TrackerSyncLog
from apps.tracker_sync.services import TrackerSyncService
from apps.tracker_sync.models import XbtFileCompatMirror, XbtFileMirror, XbtUserMirror
from apps.users.models import InviteCode, User


def build_torrent_bytes(*, private: bool = True) -> bytes:
    return flatbencode.encode(
        {
            b"announce": b"https://tracker.example/announce",
            b"info": {
                b"name": b"Example.S01E01.mkv",
                b"piece length": 262144,
                b"pieces": b"01234567890123456789",
                b"length": 1024,
                b"private": 1 if private else 0,
            },
        }
    )


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
            if XbtFileCompatMirror._meta.db_table not in existing_tables:
                cursor.execute(
                    """
                    CREATE TABLE xbt_files (
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
                existing_tables.add(XbtFileCompatMirror._meta.db_table)

    def setUp(self):
        self.client = APIClient()
        XbtFileMirror.objects.all().delete()
        XbtFileCompatMirror.objects.all().delete()
        XbtUserMirror.objects.all().delete()
        self.category = Category.objects.create(name="鍔ㄧ敾", slug="anime", sort_order=1, is_active=True)
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

    def recreate_xbt_users_table(self, *, include_can_leech: bool):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS xbt_users")
            if include_can_leech:
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
            else:
                cursor.execute(
                    """
                    CREATE TABLE xbt_users (
                        uid INTEGER PRIMARY KEY,
                        torrent_pass VARCHAR(32) NOT NULL UNIQUE,
                        downloaded BIGINT NOT NULL DEFAULT 0,
                        uploaded BIGINT NOT NULL DEFAULT 0,
                        completed INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )

    def create_release(self, *, status: str = "published", execute_on_commit: bool = False, torrent_bytes: bytes | None = None):
        self.client.force_login(self.uploader)
        torrent = SimpleUploadedFile(
            "example.torrent",
            torrent_bytes or build_torrent_bytes(),
            content_type="application/x-bittorrent",
        )
        payload = {
            "title": "娴嬭瘯璧勬簮",
            "subtitle": "WEB-DL 1080p",
            "description": "璧勬簮璇存槑",
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

    def test_public_site_settings_is_available_without_login(self):
        setting = SiteSetting.get_current()
        setting.site_name = "StarGate Subs"
        setting.site_description = "娆㈣繋鏉ュ埌娴嬭瘯绔欑偣"
        setting.site_icon_url = "https://cdn.example.com/brand/icon.png"
        setting.login_background_type = "api"
        setting.login_background_api_url = "https://cdn.example.com/backgrounds/login.jpg"
        setting.login_background_css = "linear-gradient(135deg, #020617, #1e293b)"
        setting.save(
            update_fields=[
                "site_name",
                "site_description",
                "site_icon_url",
                "login_background_type",
                "login_background_api_url",
                "login_background_css",
            ]
        )

        client = APIClient()
        response = client.get("/api/site-settings/")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(
            response.json()["data"],
            {
                "siteName": "StarGate Subs",
                "siteDescription": "娆㈣繋鏉ュ埌娴嬭瘯绔欑偣",
                "loginNotice": "",
                "allowPublicRegistration": False,
                "rssBasePath": "/rss",
                "downloadNotice": "",
                "siteIconUrl": "https://cdn.example.com/brand/icon.png",
                "siteIconFileUrl": "",
                "siteIconResolvedUrl": "https://cdn.example.com/brand/icon.png",
                "loginBackgroundType": "api",
                "loginBackgroundApiUrl": "https://cdn.example.com/backgrounds/login.jpg",
                "loginBackgroundFileUrl": "",
                "loginBackgroundResolvedUrl": "https://cdn.example.com/backgrounds/login.jpg",
                "loginBackgroundCss": "linear-gradient(135deg, #020617, #1e293b)",
            },
        )

    def test_invite_only_registration_requires_invite_code(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new-user",
                "displayName": "New User",
                "email": "new-user@example.com",
                "password": "Register123!",
                "confirmPassword": "Register123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(response.json()["code"], "validation_error")
        self.assertEqual(response.json()["message"], "当前站点仅支持邀请码注册，请输入邀请码。")

    def test_invite_only_registration_can_consume_invite_code(self):
        invite_code = InviteCode.objects.create(code="ABCD-EFGH-2345", created_by=self.admin)

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new-user",
                "displayName": "Invite User",
                "email": "new-user@example.com",
                "password": "Register123!",
                "confirmPassword": "Register123!",
                "inviteCode": "abcd efgh 2345",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["data"]["username"], "new-user")

        created_user = User.objects.get(username="new-user")
        invite_code.refresh_from_db()
        self.assertEqual(invite_code.used_by_id, created_user.id)
        self.assertIsNotNone(invite_code.used_at)
        self.assertFalse(invite_code.is_active)
        self.assertTrue(AuditLog.objects.filter(action="使用邀请码注册", target_name=invite_code.code).exists())

    def test_invite_only_registration_rejects_used_invite_code(self):
        invite_code = InviteCode.objects.create(
            code="USED-ABCD-2345",
            created_by=self.admin,
            used_by=self.user,
            used_at=timezone.now(),
            is_active=False,
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "another-user",
                "displayName": "Another User",
                "email": "another-user@example.com",
                "password": "Register123!",
                "confirmPassword": "Register123!",
                "inviteCode": invite_code.code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(response.json()["message"], "邀请码已被使用。")

    def test_public_registration_can_create_and_login_regular_user(self):
        setting = SiteSetting.get_current()
        setting.allow_public_registration = True
        setting.save(update_fields=["allow_public_registration"])

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new-user",
                "displayName": "Public User",
                "email": "new-user@example.com",
                "password": "Register123!",
                "confirmPassword": "Register123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["data"]["username"], "new-user")
        self.assertEqual(response.json()["data"]["status"], "active")

        created_user = User.objects.get(username="new-user")
        self.assertEqual(created_user.role, "user")
        self.assertTrue(AuditLog.objects.filter(action="鍒涘缓鐢ㄦ埛", target_name="new-user").exists())

        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200, me.json())
        self.assertEqual(me.json()["data"]["username"], "new-user")

    def test_can_fetch_me_with_api_token_authorization_header(self):
        response = self.client.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Token {self.user.api_token}",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["data"]["username"], "user")

    def test_admin_endpoint_accepts_x_api_key_header(self):
        response = self.client.get(
            "/api/admin/tracker-sync/overview/",
            HTTP_X_API_KEY=self.admin.api_token,
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()["data"]["summary"]["xbtSyncEnabled"])

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
                "title": "Unauthorized Release",
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
        torrent = Torrent.read_stream(response.content, validate=False)
        self.assertEqual(
            torrent.trackers[0][0],
            f"http://localhost:8000/{self.user.passkey}/announce",
        )
        self.assertTrue(torrent.private)

    def test_uploader_create_release_auto_converts_public_torrent_to_private(self):
        release = self.create_release(torrent_bytes=build_torrent_bytes(private=False))
        self.assertEqual(release.status, "published")

        with release.torrent_file.open("rb") as torrent_handle:
            stored_torrent = Torrent.read_stream(torrent_handle.read(), validate=False)

        self.assertTrue(stored_torrent.private)
        self.assertEqual(release.files.count(), 1)

    def test_uploader_can_upload_torrent_and_export_private_personalized_version(self):
        self.client.force_login(self.uploader)
        response = self.client.post(
            "/api/torrents/privatize/",
            {
                "torrentFile": SimpleUploadedFile(
                    "public.torrent",
                    build_torrent_bytes(private=False),
                    content_type="application/x-bittorrent",
                )
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)

        torrent = Torrent.read_stream(response.content, validate=False)
        self.assertTrue(torrent.private)
        self.assertEqual(torrent.trackers, [[f"http://localhost:8000/{self.uploader.passkey}/announce"]])
        self.assertTrue(
            AuditLog.objects.filter(action="绉佹湁鍖?torrent", target_type="torrent 宸ュ叿", actor=self.uploader).exists()
        )

    def test_regular_user_cannot_use_torrent_privatize_tool(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/torrents/privatize/",
            {
                "torrentFile": SimpleUploadedFile(
                    "public.torrent",
                    build_torrent_bytes(private=False),
                    content_type="application/x-bittorrent",
                )
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 403, response.content)

    def test_rss_feed_uses_passkey_download_link(self):
        release = self.create_release()
        response = self.client.get(f"/rss/all?passkey={self.user.passkey}")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn(release.title, body)
        self.assertIn(self.user.passkey, body)

    def test_rss_feed_accepts_token_query_alias(self):
        release = self.create_release()
        response = self.client.get(f"/rss/all?token={self.user.passkey}")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn(release.title, body)
        self.assertIn(self.user.passkey, body)

    def test_rss_feed_accepts_token_path_route(self):
        release = self.create_release()
        response = self.client.get(f"/rss/{self.user.passkey}/category/{self.category.slug}")
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

    def test_hide_alias_marks_release_hidden(self):
        release = self.create_release(execute_on_commit=True)
        info_hash = bytes.fromhex(release.infohash)

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"/api/releases/{release.id}/hide/")
        self.assertEqual(response.status_code, 200, response.json())

        release.refresh_from_db()
        self.assertEqual(release.status, "hidden")
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
                "title": "Broken Torrent",
                "subtitle": "WEB-DL 1080p",
                "description": "璧勬簮璇存槑",
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
                "displayName": "Duplicate Username User",
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

    def test_admin_can_create_user_with_custom_password(self):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/admin/users/",
                {
                    "username": "custom-member",
                    "displayName": "Custom Password User",
                    "email": "custom-member@example.com",
                    "role": "user",
                    "password": "Custom12345!",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())

        data = response.json()["data"]
        self.assertNotIn("initialPassword", data)

        created_user = User.objects.get(username="custom-member")
        self.assertTrue(created_user.check_password("Custom12345!"))
        self.assertEqual(XbtUserMirror.objects.get(uid=created_user.id).torrent_pass, created_user.passkey)

        self.client.logout()
        login = self.client.post(
            "/api/auth/login/",
            {"username": "custom-member", "password": "Custom12345!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.json())

    def test_admin_create_user_without_password_returns_generated_password(self):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/admin/users/",
                {
                    "username": "generated-member",
                    "displayName": "鑷姩瀵嗙爜鐢ㄦ埛",
                    "email": "generated-member@example.com",
                    "role": "user",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.json())

        data = response.json()["data"]
        self.assertIn("initialPassword", data)
        self.assertTrue(data["initialPassword"])

        created_user = User.objects.get(username="generated-member")
        self.assertTrue(created_user.check_password(data["initialPassword"]))

    def test_create_superuser_syncs_to_xbt_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            manager_user = User.objects.create_superuser(
                username="ops-admin",
                email="ops-admin@example.com",
                password="OpsAdmin12345!",
                display_name="ops-admin",
            )

        self.assertEqual(XbtUserMirror.objects.get(uid=manager_user.id).torrent_pass, manager_user.passkey)

    def test_direct_user_save_updates_xbt_user_mirror_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.user.passkey = "1" * 32
            self.user.save(update_fields=["passkey"])

        self.assertEqual(XbtUserMirror.objects.get(uid=self.user.id).torrent_pass, self.user.passkey)

    def test_admin_can_update_user_profile_fields(self):
        self.client.force_login(self.admin)
        response = self.client.patch(
            f"/api/admin/users/{self.user.id}/",
            {
                "displayName": "鏇存柊鍚庣殑鐢ㄦ埛",
                "email": "updated-user@example.com",
                "role": "uploader",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "鏇存柊鍚庣殑鐢ㄦ埛")
        self.assertEqual(self.user.email, "updated-user@example.com")
        self.assertEqual(self.user.role, "uploader")
        self.assertTrue(AuditLog.objects.filter(action="鏇存柊鐢ㄦ埛", target_name=self.user.username).exists())

    def test_admin_can_upload_site_icon_and_login_background_file(self):
        self.client.force_login(self.admin)
        icon = SimpleUploadedFile(
            "favicon.svg",
            b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><circle cx='32' cy='32' r='28'/></svg>",
            content_type="image/svg+xml",
        )
        background = SimpleUploadedFile(
            "login-bg.jpg",
            b"fake-background-image-bytes",
            content_type="image/jpeg",
        )

        response = self.client.put(
            "/api/admin/settings/",
            {
                "siteName": "Test Site",
                "siteDescription": "New login branding",
                "loginBackgroundType": "file",
                "siteIconFile": icon,
                "loginBackgroundFile": background,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["siteName"], "Test Site")
        self.assertEqual(data["siteDescription"], "New login branding")
        self.assertEqual(data["loginBackgroundType"], "file")
        self.assertIn("/media/site/branding/", data["siteIconFileUrl"])
        self.assertIn("/media/site/branding/", data["siteIconResolvedUrl"])
        self.assertIn("/media/site/login-backgrounds/", data["loginBackgroundFileUrl"])
        self.assertIn("/media/site/login-backgrounds/", data["loginBackgroundResolvedUrl"])

        setting = SiteSetting.get_current()
        self.assertTrue(bool(setting.site_icon_file))
        self.assertTrue(bool(setting.login_background_file))
        self.assertEqual(setting.login_background_type, "file")
        self.assertTrue(AuditLog.objects.filter(action="鏇存柊绔欑偣璁剧疆", target_type="绔欑偣璁剧疆").exists())

    def test_admin_can_switch_login_background_to_css_mode(self):
        self.client.force_login(self.admin)
        response = self.client.put(
            "/api/admin/settings/",
            {
                "loginBackgroundType": "css",
                "loginBackgroundCss": "linear-gradient(120deg, #020617 0%, #172554 100%)",
                "loginBackgroundApiUrl": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        setting = SiteSetting.get_current()
        self.assertEqual(setting.login_background_type, "css")
        self.assertEqual(setting.login_background_css, "linear-gradient(120deg, #020617 0%, #172554 100%)")

    def test_admin_can_toggle_public_registration(self):
        self.client.force_login(self.admin)
        response = self.client.put(
            "/api/admin/settings/",
            {
                "allowPublicRegistration": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()["data"]["allowPublicRegistration"], True)

        setting = SiteSetting.get_current()
        self.assertTrue(setting.allow_public_registration)

    def test_admin_can_generate_and_revoke_invite_codes(self):
        self.client.force_login(self.admin)
        expires_at = (timezone.now() + timedelta(days=7)).isoformat()

        create_response = self.client.post(
            "/api/admin/invite-codes/",
            {
                "count": 2,
                "note": "April members",
                "expiresAt": expires_at,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.json())
        self.assertEqual(len(create_response.json()["data"]), 2)

        created_id = create_response.json()["data"][0]["id"]
        list_response = self.client.get("/api/admin/invite-codes/")
        self.assertEqual(list_response.status_code, 200, list_response.json())
        self.assertGreaterEqual(len(list_response.json()["data"]), 2)
        self.assertTrue(AuditLog.objects.filter(action="鐢熸垚閭€璇风爜").exists())

        revoke_response = self.client.post(f"/api/admin/invite-codes/{created_id}/revoke/")
        self.assertEqual(revoke_response.status_code, 200, revoke_response.json())
        self.assertEqual(revoke_response.json()["data"]["status"], "revoked")

        revoked_code = InviteCode.objects.get(pk=created_id)
        self.assertFalse(revoked_code.is_active)
        self.assertTrue(AuditLog.objects.filter(action="鍋滅敤閭€璇风爜", target_name=revoked_code.code).exists())

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

    def test_request_logging_identifies_api_token_actor_without_exposing_secret(self):
        with self.assertLogs("apps.request", level="INFO") as captured:
            response = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Token {self.user.api_token}")
        self.assertEqual(response.status_code, 200)

        combined = "\n".join(captured.output)
        self.assertIn("actor=api-token:user", combined)
        self.assertNotIn(self.user.api_token, combined)

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
            {"name": "Documentary", "slug": "documentary"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(
            AuditLog.objects.filter(action="鍒涘缓鍒嗙被", target_type="鍒嗙被", target_name="Documentary").exists()
        )

    def test_admin_can_set_category_sort_order_and_visibility(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/admin/categories/",
            {
                "name": "Documentary",
                "slug": "documentary",
                "sortOrder": 9,
                "isActive": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        category = Category.objects.get(slug="documentary")
        self.assertEqual(category.sort_order, 9)
        self.assertFalse(category.is_active)
        self.assertEqual(
            response.json()["data"],
            {
                "id": category.id,
                "name": "Documentary",
                "slug": "documentary",
                "sortOrder": 9,
                "isActive": False,
            },
        )

        public_categories = self.client.get("/api/categories/")
        self.assertEqual(public_categories.status_code, 200, public_categories.json())
        self.assertNotIn("documentary", [item["slug"] for item in public_categories.json()["data"]])

    def test_admin_can_update_category_sort_order_and_visibility(self):
        category = Category.objects.create(name="Documentary", slug="documentary", sort_order=9, is_active=False)

        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/admin/categories/",
            {
                "id": category.id,
                "name": "Documentary",
                "slug": "documentary",
                "sortOrder": 3,
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.json())

        category.refresh_from_db()
        self.assertEqual(category.sort_order, 3)
        self.assertTrue(category.is_active)

        public_categories = self.client.get("/api/categories/")
        self.assertEqual(public_categories.status_code, 200, public_categories.json())
        self.assertIn("documentary", [item["slug"] for item in public_categories.json()["data"]])

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

    def test_admin_can_get_tracker_sync_overview(self):
        release = self.create_release(execute_on_commit=True)
        TrackerSyncLog.objects.create(
            scope="release",
            target_name=release.title,
            status="failed",
            message="manual failure",
            release=release,
        )

        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/tracker-sync/overview/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertTrue(data["summary"]["xbtSyncEnabled"])
        self.assertEqual(data["summary"]["failedCount"], 1)
        self.assertGreaterEqual(data["summary"]["successCount"], 1)
        self.assertEqual(
            data["summary"]["pendingCount"],
            data["summary"]["warningCount"] + data["summary"]["failedCount"],
        )
        self.assertTrue(any(item["scope"] == "release" for item in data["latestLogs"]))
        self.assertEqual(data["failedLogs"][0]["releaseId"], release.id)
        self.assertTrue(data["failedLogs"][0]["retryable"])

    def test_admin_can_get_tracker_sync_user_detail(self):
        TrackerSyncService.sync_user(self.user)

        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/tracker-sync/users/{self.user.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["user"]["id"], self.user.id)
        self.assertEqual(data["user"]["username"], self.user.username)
        self.assertEqual(data["user"]["displayName"], self.user.display_name)
        self.assertEqual(data["trackerSync"]["status"], "success")
        self.assertEqual(data["xbtUser"]["state"], "enabled")
        self.assertEqual(data["recentLogs"][0]["userId"], self.user.id)
        self.assertTrue(data["recentLogs"][0]["retryable"])

    def test_admin_can_run_tracker_sync_for_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(f"/api/admin/tracker-sync/users/{self.user.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["scope"], "user")
        self.assertEqual(data["userId"], self.user.id)
        self.assertTrue(data["retryable"])
        self.assertEqual(XbtUserMirror.objects.get(uid=self.user.id).torrent_pass, self.user.passkey)

    def test_tracker_sync_user_supports_legacy_xbt_users_schema_without_can_leech(self):
        self.recreate_xbt_users_table(include_can_leech=False)
        self.addCleanup(self.recreate_xbt_users_table, include_can_leech=True)

        active_log = TrackerSyncService.sync_user(self.user)
        self.assertEqual(active_log.status, "success")

        with connection.cursor() as cursor:
            cursor.execute("SELECT uid, torrent_pass FROM xbt_users WHERE uid = %s", [self.user.id])
            active_row = cursor.fetchone()
        self.assertEqual(active_row, (self.user.id, self.user.passkey))

        snapshot = TrackerSyncService.get_user_sync_snapshot(self.user)
        self.assertEqual(snapshot["xbtUser"]["state"], "enabled")
        self.assertEqual(snapshot["xbtUser"]["canLeech"], True)

        self.user.status = "disabled"
        self.user.save(update_fields=["status"])

        disabled_log = TrackerSyncService.sync_user(self.user)
        self.assertEqual(disabled_log.status, "success")

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM xbt_users WHERE uid = %s", [self.user.id])
            remaining_rows = cursor.fetchone()[0]
        self.assertEqual(remaining_rows, 0)

    def test_admin_can_get_tracker_sync_release_detail(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/tracker-sync/releases/{release.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["release"]["id"], release.id)
        self.assertEqual(data["release"]["title"], release.title)
        self.assertEqual(data["release"]["infohash"], release.infohash)
        self.assertEqual(data["trackerSync"]["status"], "success")
        self.assertEqual(data["xbtFile"]["state"], "whitelisted")
        self.assertEqual(data["recentLogs"][0]["releaseId"], release.id)
        self.assertTrue(data["recentLogs"][0]["retryable"])

    def test_release_sync_can_write_to_xbt_files_compatible_table(self):
        release = self.create_release(status="published")
        info_hash = bytes.fromhex(release.infohash)

        with patch.object(TrackerSyncService, "_xbt_file_model", return_value=XbtFileCompatMirror):
            log = TrackerSyncService.sync_release(release)

        self.assertEqual(log.status, "success")
        self.assertTrue(XbtFileCompatMirror.objects.filter(info_hash=info_hash, flags=0).exists())

        release.status = "hidden"
        release.save(update_fields=["status"])
        with patch.object(TrackerSyncService, "_xbt_file_model", return_value=XbtFileCompatMirror):
            log = TrackerSyncService.sync_release(release)

        self.assertEqual(log.status, "success")
        self.assertTrue(XbtFileCompatMirror.objects.filter(info_hash=info_hash, flags=1).exists())

    def test_admin_can_retry_tracker_sync_log_for_release(self):
        release = self.create_release(execute_on_commit=True)
        info_hash = bytes.fromhex(release.infohash)
        XbtFileMirror.objects.filter(info_hash=info_hash).delete()
        failed_log = TrackerSyncLog.objects.create(
            scope="release",
            target_name=release.title,
            status="failed",
            message="manual failure",
            release=release,
        )

        self.client.force_login(self.admin)
        response = self.client.post(f"/api/admin/tracker-sync/logs/{failed_log.id}/retry/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertEqual(data["scope"], "release")
        self.assertEqual(data["releaseId"], release.id)
        self.assertTrue(data["retryable"])
        self.assertTrue(XbtFileMirror.objects.filter(info_hash=info_hash, flags=0).exists())

    def test_tracker_sync_log_list_exposes_retry_metadata(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/tracker-sync/logs/?scope=release")
        self.assertEqual(response.status_code, 200, response.json())

        item = response.json()["data"][0]
        self.assertEqual(item["scope"], "release")
        self.assertEqual(item["releaseId"], release.id)
        self.assertTrue(item["retryable"])

    def test_tracker_sync_log_list_can_filter_by_user_id(self):
        TrackerSyncService.sync_user(self.user)
        TrackerSyncService.sync_user(self.uploader)

        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/tracker-sync/logs/?scope=user&userId={self.user.id}")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertTrue(data)
        self.assertTrue(all(item["userId"] == self.user.id for item in data))

    def test_tracker_sync_log_list_can_filter_by_release_id(self):
        release = self.create_release(execute_on_commit=True)
        second_release = self.create_release(
            status="draft",
            execute_on_commit=True,
            torrent_bytes=build_torrent_bytes(private=True).replace(b"Example.S01E01.mkv", b"Example.S01E02.mkv"),
        )

        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/tracker-sync/logs/?scope=release&releaseId={release.id}")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertTrue(data)
        self.assertTrue(all(item["releaseId"] == release.id for item in data))
        self.assertNotIn(second_release.id, [item["releaseId"] for item in data if item["releaseId"] is not None])

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

    def test_user_can_get_and_reset_own_api_token(self):
        old_token = self.user.api_token
        self.client.force_login(self.user)

        get_response = self.client.get("/api/me/api-token/")
        self.assertEqual(get_response.status_code, 200, get_response.json())
        self.assertEqual(get_response.json()["data"]["apiToken"], old_token)

        reset_response = self.client.post("/api/me/api-token/")
        self.assertEqual(reset_response.status_code, 200, reset_response.json())

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.api_token, old_token)
        self.assertEqual(reset_response.json()["data"]["apiToken"], self.user.api_token)

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
        self.assertIn("/api/torrents/privatize/", schema["paths"])
        self.assertIn("/api/admin/tracker-sync/full/", schema["paths"])
        self.assertIn("/api/admin/tracker-sync/overview/", schema["paths"])
        self.assertIn("get", schema["paths"]["/api/admin/tracker-sync/users/{user_id}/"])
        self.assertIn("get", schema["paths"]["/api/admin/tracker-sync/releases/{release_id}/"])
        self.assertIn("/api/admin/tracker-sync/logs/{log_id}/retry/", schema["paths"])
        self.assertIn("sessionCookieAuth", schema["components"]["securitySchemes"])
        self.assertIn("userApiTokenAuth", schema["components"]["securitySchemes"])
        self.assertIn("userApiKeyAuth", schema["components"]["securitySchemes"])
        self.assertIn("multipart/form-data", schema["paths"]["/api/releases/"]["post"]["requestBody"]["content"])
        self.assertIn("multipart/form-data", schema["paths"]["/api/torrents/privatize/"]["post"]["requestBody"]["content"])

    def test_redoc_route_is_available(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<redoc ", response.content.decode("utf-8"))

    def test_regular_user_cannot_access_admin_tracker_sync_overview(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/admin/tracker-sync/overview/")
        self.assertEqual(response.status_code, 403, response.json())
        self.assertEqual(response.json()["code"], "permission_denied")

    def test_uploader_cannot_access_admin_user_list(self):
        self.client.force_login(self.uploader)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 403, response.json())
        self.assertEqual(response.json()["code"], "permission_denied")

