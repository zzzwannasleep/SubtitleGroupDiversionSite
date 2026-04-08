from django.urls import path

from apps.rss.views import AllFeedView, CategoryFeedView, TagFeedView


urlpatterns = [
    path("all", AllFeedView.as_view(), name="rss-all"),
    path("category/<slug:slug>", CategoryFeedView.as_view(), name="rss-category"),
    path("tag/<slug:slug>", TagFeedView.as_view(), name="rss-tag"),
]
