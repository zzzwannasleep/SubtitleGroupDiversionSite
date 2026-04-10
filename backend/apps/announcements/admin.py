from django.contrib import admin

from apps.announcements.models import Announcement, SiteSetting


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "audience", "updated_at")
    list_filter = ("status", "audience")
    search_fields = ("title", "content")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("site_name", "login_background_type", "rss_base_path", "updated_at")
