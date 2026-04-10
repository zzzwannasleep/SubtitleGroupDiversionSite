from django.urls import path

from apps.authx.views import ChangePasswordView, LoginView, LogoutView, MeView, RegisterView


urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
]
