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
    # Registration OTP
    # =========================================

    path(
        "verify/",
        views.VerifyRegistrationView.as_view(),
        name="verify",
    ),

    path(
        "verify/resend/",
        views.ResendOTPView.as_view(),
        name="resend_otp",
    ),

    # =========================================
    # Forgot Password
    # =========================================

    path(
        "forgot-password/",
        views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),

    path(
        "forgot-password/verify/",
        views.ForgotPasswordVerifyView.as_view(),
        name="forgot_password_verify",
    ),

    path(
        "forgot-password/verify/resend/",
        views.ResendPasswordResetOTPView.as_view(),
        name="forgot_password_resend",
    ),

    path(
        "forgot-password/reset/",
        views.ResetPasswordView.as_view(),
        name="reset_password",
    ),

    # =========================================
    # Logout
    # =========================================

    path(
        "logout/",
        views.UserLogout.as_view(),
        name="logout",
    ),
]
