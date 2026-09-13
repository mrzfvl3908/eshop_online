from django.urls import path

from . import views

app_name = "accounts_app"

urlpatterns = [

    # =========================================
    # Login
    # =========================================

    path(
        "login/",
        views.UserLogin.as_view(),
        name="login",
    ),

    # =========================================
    # Register
    # =========================================

    path(
        "register/",
        views.UserRegister.as_view(),
        name="register",
    ),

    # =========================================
    # Verify OTP
    # =========================================

    path(
        "verify/",
        views.VerifyRegistrationView.as_view(),
        name="verify",
    ),

    # =========================================
    # Resend OTP
    # =========================================

    path(
        "verify/resend/",
        views.ResendOTPView.as_view(),
        name="resend_otp",
    ),
    path("logout/", views.UserLogout.as_view(), name="logout"),
]
