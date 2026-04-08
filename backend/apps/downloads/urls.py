from django.urls import path

from apps.downloads.views import MyDownloadListView, ReleaseDownloadView


urlpatterns = [
    path("releases/<int:release_id>/download/", ReleaseDownloadView.as_view(), name="release-download"),
    path("me/downloads/", MyDownloadListView.as_view(), name="my-downloads"),
]
