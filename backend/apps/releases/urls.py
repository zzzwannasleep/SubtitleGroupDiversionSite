from django.urls import path

from apps.releases.views import (
    AdminCategoryListCreateView,
    AdminReleaseListView,
    AdminTagListCreateView,
    CategoryListView,
    HomeDataView,
    MyReleaseListView,
    ReleaseCollectionView,
    ReleaseDetailView,
    ReleaseHideView,
    ReleaseVisibilityView,
    TagListView,
)


urlpatterns = [
    path("home/", HomeDataView.as_view(), name="home-data"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("tags/", TagListView.as_view(), name="tags"),
    path("releases/", ReleaseCollectionView.as_view(), name="releases"),
    path("releases/<int:release_id>/", ReleaseDetailView.as_view(), name="release-detail"),
    path("releases/<int:release_id>/hide/", ReleaseHideView.as_view(), name="release-hide"),
    path("releases/<int:release_id>/visibility/", ReleaseVisibilityView.as_view(), name="release-visibility"),
    path("me/releases/", MyReleaseListView.as_view(), name="my-releases"),
    path("admin/releases/", AdminReleaseListView.as_view(), name="admin-releases"),
    path("admin/categories/", AdminCategoryListCreateView.as_view(), name="admin-categories"),
    path("admin/tags/", AdminTagListCreateView.as_view(), name="admin-tags"),
]
