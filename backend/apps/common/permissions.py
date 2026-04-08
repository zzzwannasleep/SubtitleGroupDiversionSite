from rest_framework.permissions import BasePermission


class IsActiveAuthenticated(BasePermission):
    message = "请先登录有效账户。"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "status", None) == "active")


class IsAdminRole(IsActiveAuthenticated):
    message = "仅管理员可执行该操作。"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "admin"


class IsUploaderOrAdmin(IsActiveAuthenticated):
    message = "仅上传者或管理员可执行该操作。"

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in {"admin", "uploader"}


class IsReleaseOwnerOrAdmin(IsActiveAuthenticated):
    message = "仅资源发布者或管理员可执行该操作。"

    def has_object_permission(self, request, view, obj):
        return request.user.role == "admin" or obj.created_by_id == request.user.id
