from django.urls import path
from . import views

app_name = 'accounts_app'

urlpatterns = [
    path('login/', views.UserLogin.as_view(), name='login'),          # ورود با رمز عبور (قدیمی)
    path('otp-login/', views.OTPLoginView.as_view(), name='otp_login'),  # ورود با کد (جدید)
]