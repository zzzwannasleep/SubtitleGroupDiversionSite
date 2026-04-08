from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor_name", "action", "target_type", "target_name", "created_at")
    list_filter = ("target_type", "created_at")
    search_fields = ("actor_name", "action", "target_name", "detail")
