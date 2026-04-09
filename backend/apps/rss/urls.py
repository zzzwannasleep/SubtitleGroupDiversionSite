from django.urls import path

from apps.rss.views import (
    AllFeedTokenPathView,
    AllFeedView,
    CategoryFeedTokenPathView,
    CategoryFeedView,
    TagFeedTokenPathView,
    TagFeedView,
)


urlpatterns = [
    path("all", AllFeedView.as_view(), name="rss-all"),
    path("category/<slug:slug>", CategoryFeedView.as_view(), name="rss-category"),
    path("tag/<slug:slug>", TagFeedView.as_view(), name="rss-tag"),
    path("<slug:token>/all", AllFeedTokenPathView.as_view(), name="rss-all-token-path"),
    path("<slug:token>/category/<slug:slug>", CategoryFeedTokenPathView.as_view(), name="rss-category-token-path"),
    path("<slug:token>/tag/<slug:slug>", TagFeedTokenPathView.as_view(), name="rss-tag-token-path"),
]
