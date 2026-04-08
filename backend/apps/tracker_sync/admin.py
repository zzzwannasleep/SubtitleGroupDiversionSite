from django.contrib import admin

from apps.tracker_sync.models import TrackerSyncLog, XbtFileMirror, XbtUserMirror


@admin.register(TrackerSyncLog)
class TrackerSyncLogAdmin(admin.ModelAdmin):
    list_display = ("scope", "target_name", "status", "updated_at")
    list_filter = ("scope", "status")
    search_fields = ("target_name", "message")


@admin.register(XbtUserMirror)
class XbtUserMirrorAdmin(admin.ModelAdmin):
    list_display = ("uid", "torrent_pass", "can_leech", "downloaded", "uploaded")
    search_fields = ("uid", "torrent_pass")


@admin.register(XbtFileMirror)
class XbtFileMirrorAdmin(admin.ModelAdmin):
    list_display = ("info_hash", "seeders", "leechers", "completed", "flags", "mtime")
