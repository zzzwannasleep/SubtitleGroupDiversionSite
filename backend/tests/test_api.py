from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.common.torrent import bencode
from apps.releases.models import Category, Release, Tag
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
