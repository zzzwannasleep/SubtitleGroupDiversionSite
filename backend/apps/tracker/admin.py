from django.contrib import admin

from apps.tracker.models import TrackerTorrentSync


@admin.register(TrackerTorrentSync)
class TrackerTorrentSyncAdmin(admin.ModelAdmin):
    list_display = ("release", "infohash", "is_whitelisted", "last_synced_at")
    list_filter = ("is_whitelisted",)
    search_fields = ("infohash", "release__title", "release__created_by__username")
    readonly_fields = (
        "release",
        "infohash",
        "last_synced_at",
        "last_error",
        "last_scrape_at",
        "last_scrape_seeders",
        "last_scrape_leechers",
        "last_scrape_completed",
    )

