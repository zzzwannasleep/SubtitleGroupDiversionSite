from django.contrib import admin

from apps.releases.models import Category, Release, ReleaseFile, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    search_fields = ("name", "slug")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


class ReleaseFileInline(admin.TabularInline):
    model = ReleaseFile
    extra = 0


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "created_by", "published_at", "download_count")
    list_filter = ("status", "category")
    search_fields = ("title", "subtitle", "description", "infohash")
    filter_horizontal = ("tags",)
    inlines = [ReleaseFileInline]
