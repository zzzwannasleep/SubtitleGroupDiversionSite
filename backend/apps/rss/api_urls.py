from django.urls import path

from apps.rss.views import RssOverviewView


urlpatterns = [
    path("rss/overview/", RssOverviewView.as_view(), name="rss-overview"),
]
