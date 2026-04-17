import json
import os
import tempfile
from datetime import timedelta
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from torf import Torrent, _flatbencode as flatbencode

from apps.announcements.models import SiteSetting
from apps.audit.models import AuditLog
from apps.common.throttles import LoginRateThrottle
from apps.downloads.models import DownloadLog
from apps.releases.models import Category, Release, Tag
from apps.users.models import InviteCode, User


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


@override_settings(MEDIA_ROOT="test-media")
class ApiFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.client = APIClient()
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

    def test_create_superuser_sets_site_admin_role(self):
        superuser = User.objects.create_superuser(
            username="root",
            password="Root12345!",
            email="root@example.com",
        )

        self.assertEqual(superuser.role, "admin")
        self.assertEqual(superuser.status, "active")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

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
        self.assertEqual(response.json()["message"], "参数校验失败。")

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
        self.assertTrue(AuditLog.objects.filter(action="创建用户", target_name="new-user").exists())

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
            "/api/admin/dashboard/",
            HTTP_X_API_KEY=self.admin.api_token,
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertIn("stats", response.json()["data"])

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

    def test_uploader_can_create_release_with_minimal_fields(self):
        self.client.force_login(self.uploader)
        torrent = SimpleUploadedFile("example.torrent", build_torrent_bytes(), content_type="application/x-bittorrent")
        response = self.client.post(
            "/api/releases/",
            {
                "torrentFile": torrent,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(response.json()["data"]["title"], "Example.S01E01.mkv")
        self.assertEqual(response.json()["data"]["subtitle"], "")
        self.assertEqual(response.json()["data"]["description"], "")
        self.assertEqual(response.json()["data"]["category"]["slug"], self.category.slug)

    def test_uploader_can_create_release_and_download_original_torrent(self):
        release = self.create_release()
        self.client.force_login(self.user)
        response = self.client.get(f"/api/releases/{release.id}/download/")
        self.assertEqual(response.status_code, 200)
        torrent = Torrent.read_stream(response.content, validate=False)
        self.assertEqual(torrent.trackers[0][0], "https://example.com/announce")
        self.assertTrue(torrent.private)

    def test_uploader_create_release_preserves_public_torrent_metadata(self):
        release = self.create_release(torrent_bytes=build_torrent_bytes(private=False))
        self.assertEqual(release.status, "published")

        with release.torrent_file.open("rb") as torrent_handle:
            stored_torrent = Torrent.read_stream(torrent_handle.read(), validate=False)

        self.assertFalse(stored_torrent.private)
        self.assertEqual(stored_torrent.trackers[0][0], "https://example.com/announce")
        self.assertEqual(release.files.count(), 1)

    def test_uploader_can_replace_torrent_file_on_edit(self):
        release = self.create_release()
        old_infohash = release.infohash

        self.client.force_login(self.uploader)
        response = self.client.patch(
            f"/api/releases/{release.id}/",
            {
                "title": "更新后的资源标题",
                "subtitle": "WEB-DL 1080p",
                "description": "更新后的资源说明",
                "categorySlug": self.category.slug,
                "tagSlugs": [self.tag.slug],
                "status": "published",
                "torrentFile": SimpleUploadedFile(
                    "replacement.torrent",
                    build_torrent_bytes(private=False).replace(b"Example.S01E01.mkv", b"Example.S01E02.mkv"),
                    content_type="application/x-bittorrent",
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.json())

        release.refresh_from_db()
        self.assertNotEqual(release.infohash, old_infohash)
        self.assertEqual(release.title, "更新后的资源标题")

        with release.torrent_file.open("rb") as torrent_handle:
            stored_torrent = Torrent.read_stream(torrent_handle.read(), validate=False)

        self.assertFalse(stored_torrent.private)
        self.assertEqual(stored_torrent.trackers[0][0], "https://example.com/announce")

    def test_rss_feed_uses_public_download_link(self):
        release = self.create_release()
        response = self.client.get("/rss/all")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn(release.title, body)
        self.assertIn(f"/api/releases/{release.id}/download/", body)
        self.assertNotIn("passkey=", body)

    def test_anonymous_user_can_download_published_release(self):
        release = self.create_release()
        client = APIClient()
        response = client.get(f"/api/releases/{release.id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DownloadLog.objects.filter(release=release, user__isnull=True).count(), 1)

    def test_draft_release_can_publish_without_tracker_side_effects(self):
        release = self.create_release(status="draft", execute_on_commit=True)
        self.assertEqual(release.status, "draft")

        self.client.force_login(self.uploader)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                f"/api/releases/{release.id}/",
                {"status": "published"},
                format="json",
            )
        self.assertEqual(response.status_code, 200, response.json())
        release.refresh_from_db()
        self.assertEqual(release.status, "published")

    def test_hidden_release_marks_release_hidden(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/api/releases/{release.id}/visibility/",
                {"status": "hidden"},
                format="json",
            )
        self.assertEqual(response.status_code, 200, response.json())
        release.refresh_from_db()
        self.assertEqual(release.status, "hidden")

    def test_hide_alias_marks_release_hidden(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"/api/releases/{release.id}/hide/")
        self.assertEqual(response.status_code, 200, response.json())

        release.refresh_from_db()
        self.assertEqual(release.status, "hidden")

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
        self.assertTrue(AuditLog.objects.filter(action="更新用户", target_name=self.user.username).exists())

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
        self.assertTrue(AuditLog.objects.filter(action="更新站点设置", target_type="站点设置").exists())

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
        self.assertTrue(AuditLog.objects.filter(action="生成邀请码").exists())

        revoke_response = self.client.post(f"/api/admin/invite-codes/{created_id}/revoke/")
        self.assertEqual(revoke_response.status_code, 200, revoke_response.json())
        self.assertEqual(revoke_response.json()["data"]["status"], "revoked")

        revoked_code = InviteCode.objects.get(pk=created_id)
        self.assertFalse(revoked_code.is_active)
        self.assertTrue(AuditLog.objects.filter(action="停用邀请码", target_name=revoked_code.code).exists())

    def test_admin_can_disable_and_enable_user_with_explicit_routes(self):
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            disable = self.client.post(f"/api/admin/users/{self.user.id}/disable/")
        self.assertEqual(disable.status_code, 200, disable.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.status, "disabled")

        with self.captureOnCommitCallbacks(execute=True):
            enable = self.client.post(f"/api/admin/users/{self.user.id}/enable/")
        self.assertEqual(enable.status_code, 200, enable.json())

        self.user.refresh_from_db()
        self.assertEqual(self.user.status, "active")

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
            AuditLog.objects.filter(action="创建分类", target_type="分类", target_name="Documentary").exists()
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

    def test_admin_user_detail_excludes_tracker_sync_snapshot(self):
        self.client.force_login(self.admin)
        response = self.client.get(f"/api/admin/users/{self.user.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertNotIn("trackerSync", data)
        self.assertNotIn("xbtUser", data)
        self.assertNotIn("passkey", data)

    def test_release_detail_for_owner_excludes_tracker_sync_snapshot(self):
        release = self.create_release(execute_on_commit=True)

        self.client.force_login(self.uploader)
        response = self.client.get(f"/api/releases/{release.id}/")
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()["data"]
        self.assertNotIn("trackerSync", data)
        self.assertNotIn("xbtFile", data)
        self.assertEqual(data["infohash"], release.infohash)

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
        self.assertIn("/api/releases/{release_id}/download/", schema["paths"])
        self.assertIn("/api/admin/dashboard/", schema["paths"])
        self.assertIn("sessionCookieAuth", schema["components"]["securitySchemes"])
        self.assertIn("userApiTokenAuth", schema["components"]["securitySchemes"])
        self.assertIn("userApiKeyAuth", schema["components"]["securitySchemes"])
        self.assertIn("multipart/form-data", schema["paths"]["/api/releases/"]["post"]["requestBody"]["content"])
        self.assertNotIn("/api/torrents/privatize/", schema["paths"])
        self.assertNotIn("/api/admin/tracker-sync/overview/", schema["paths"])

    def test_redoc_route_is_available(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<redoc ", response.content.decode("utf-8"))

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/admin/dashboard/")
        self.assertEqual(response.status_code, 403, response.json())
        self.assertEqual(response.json()["code"], "permission_denied")

    def test_uploader_cannot_access_admin_user_list(self):
        self.client.force_login(self.uploader)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 403, response.json())
        self.assertEqual(response.json()["code"], "permission_denied")

