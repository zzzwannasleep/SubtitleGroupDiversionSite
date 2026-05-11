from django.urls import path

from apps.rss.views import (
    CategoryFeedView,
    PersonalAllFeedView,
    TagFeedView,
)


urlpatterns = [
    path("passkey/<str:passkey>/all", PersonalAllFeedView.as_view(), name="rss-personal-all"),
    path("category/<slug:slug>", CategoryFeedView.as_view(), name="rss-category"),
    path("tag/<slug:slug>", TagFeedView.as_view(), name="rss-tag"),
]
