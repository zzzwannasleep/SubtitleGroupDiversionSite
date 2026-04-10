from django.urls import path

from apps.announcements.views import (
    AdminAnnouncementListCreateView,
    PublicSiteSettingView,
    SiteSettingView,
    VisibleAnnouncementListView,
)


urlpatterns = [
    path("announcements/visible/", VisibleAnnouncementListView.as_view(), name="visible-announcements"),
    path("site-settings/", PublicSiteSettingView.as_view(), name="public-site-settings"),
    path("admin/announcements/", AdminAnnouncementListCreateView.as_view(), name="admin-announcements"),
    path("admin/settings/", SiteSettingView.as_view(), name="admin-settings"),
]
