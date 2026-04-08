from django.urls import path

from apps.announcements.views import AdminAnnouncementListCreateView, SiteSettingView, VisibleAnnouncementListView


urlpatterns = [
    path("announcements/visible/", VisibleAnnouncementListView.as_view(), name="visible-announcements"),
    path("admin/announcements/", AdminAnnouncementListCreateView.as_view(), name="admin-announcements"),
    path("admin/settings/", SiteSettingView.as_view(), name="admin-settings"),
]
