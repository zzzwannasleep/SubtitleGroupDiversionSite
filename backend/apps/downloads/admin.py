from django.contrib import admin

from apps.downloads.models import DownloadLog


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ("user", "release", "downloaded_at", "ip_address")
    list_filter = ("downloaded_at",)
    search_fields = ("user__username", "release__title", "ip_address")
