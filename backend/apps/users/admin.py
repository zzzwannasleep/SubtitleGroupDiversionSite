from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import InviteCode, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "display_name", "email", "role", "status", "is_staff", "last_login")
    list_filter = ("role", "status", "is_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("站点字段", {"fields": ("display_name", "role", "status", "passkey")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("站点字段", {"fields": ("display_name", "email", "role", "status", "passkey")}),
    )
    search_fields = ("username", "display_name", "email", "passkey")


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "state", "is_active", "expires_at", "created_by", "used_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "note", "created_by__username", "used_by__username")
