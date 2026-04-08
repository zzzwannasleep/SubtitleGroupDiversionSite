from django.urls import path

from apps.audit.views import AuditLogListView


urlpatterns = [
    path("admin/audit-logs/", AuditLogListView.as_view(), name="audit-logs"),
]
