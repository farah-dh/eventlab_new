from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from ..views import (
    LoginView, RegisterView, LogoutView,
    PasswordResetRequestView, PasswordResetConfirmView,
    OrganizerLoginView, OrganizerTwoFAVerifyLoginView, OrganizerTwoFAResendOTPView,
    TwoFAVerifyLoginView, TwoFAResendOTPView,
    TwoFAEnableView, TwoFAEnableConfirmView,
    TwoFADisableView, TwoFAStatusView,
)

urlpatterns = [
    path("login/",                        LoginView.as_view(),                     name="auth-login"),
    path("register/",                     RegisterView.as_view(),                  name="auth-register"),
    path("logout/",                       LogoutView.as_view(),                    name="auth-logout"),
    path("token/refresh/",                TokenRefreshView.as_view(),              name="token-refresh"),
    path("password/reset/",               PasswordResetRequestView.as_view(),      name="password-reset"),
    path("password/confirm/",             PasswordResetConfirmView.as_view(),      name="password-reset-confirm"),

    path("organizer/login/",              OrganizerLoginView.as_view(),            name="organizer-login"),
    path("organizer/2fa/verify/",         OrganizerTwoFAVerifyLoginView.as_view(), name="organizer-2fa-verify"),
    path("organizer/2fa/resend/",         OrganizerTwoFAResendOTPView.as_view(),   name="organizer-2fa-resend"),
    path("organizer/2fa/status/",         TwoFAStatusView.as_view(),               name="organizer-2fa-status"),
    path("organizer/2fa/enable/",         TwoFAEnableView.as_view(),               name="organizer-2fa-enable"),
    path("organizer/2fa/enable/confirm/", TwoFAEnableConfirmView.as_view(),        name="organizer-2fa-enable-confirm"),
    path("organizer/2fa/disable/",        TwoFADisableView.as_view(),              name="organizer-2fa-disable"),

    path("2fa/verify/",                   TwoFAVerifyLoginView.as_view(),          name="2fa-verify"),
    path("2fa/resend/",                   TwoFAResendOTPView.as_view(),            name="2fa-resend"),
    path("2fa/status/",                   TwoFAStatusView.as_view(),               name="2fa-status"),
    path("2fa/enable/",                   TwoFAEnableView.as_view(),               name="2fa-enable"),
    path("2fa/enable/confirm/",           TwoFAEnableConfirmView.as_view(),        name="2fa-enable-confirm"),
    path("2fa/disable/",                  TwoFADisableView.as_view(),              name="2fa-disable"),
]
