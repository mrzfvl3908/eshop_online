import secrets
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView, View
from django.contrib.auth.hashers import (
    make_password,
    check_password,
)
from .forms import (
    LoginForm,
    RegisterForm,
    OTPVerificationForm,
    ForgotPasswordPhoneForm,
    ForgotPasswordOTPForm,
    ResetPasswordForm,
)
from .models import (
    User,
    RegistrationVerification,
    PasswordResetVerification,
)
from .sms import send_otp_sms


def get_client_ip(request):
    """
    دریافت IP کاربر.

    در Production اگر پشت Reverse Proxy هستی،
    بهتر است فقط هدرهای Proxy مورد اعتماد را استفاده کنی.
    """

    return (
            request.META.get("HTTP_X_FORWARDED_FOR", "")
            .split(",")[0]
            .strip()
            or request.META.get("REMOTE_ADDR", "")
    )


def rate_limit(
        key,
        limit,
        window,
):
    """
    محدود کردن تعداد درخواست‌ها.

    True  = اجازه دارد
    False = محدود شده
    """

    if not getattr(
            settings,
            "AUTH_RATE_LIMIT_ENABLED",
            True,
    ):
        return True

    cache_key = f"auth-rate:{key}"

    try:

        if cache.add(
                cache_key,
                1,
                timeout=window,
        ):
            return True

        current = cache.incr(cache_key)

        return current <= limit

    except Exception:

        # اگر Cache موقتاً مشکل داشت،
        # احراز هویت را کاملاً از کار نمی‌اندازیم.
        return True


# ==================================================
# Login
# ==================================================

class UserLogin(LoginView):
    template_name = "accounts_app/login.html"

    authentication_form = LoginForm

    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy(
            "home_app:home"
        )

    def form_valid(self, form):

        phone = form.cleaned_data.get(
            "username"
        )

        ip = get_client_ip(
            self.request
        )

        key = f"login:{phone}:{ip}"

        if not rate_limit(
                key=key,
                limit=settings.LOGIN_RATE_LIMIT,
                window=settings.LOGIN_RATE_LIMIT_WINDOW,
        ):
            form.add_error(
                None,
                "تعداد تلاش‌های ورود بیش از حد مجاز است. لطفاً بعداً دوباره تلاش کنید."
            )

            return self.form_invalid(form)

        response = super().form_valid(form)

        remember_me = form.cleaned_data.get(
            "remember_me",
            False
        )

        if remember_me:

            self.request.session.set_expiry(
                5 * 24 * 60 * 60
            )

        else:

            self.request.session.set_expiry(0)

        return response


# ==================================================
# Register - Step 1
# ==================================================

class UserRegister(CreateView):
    form_class = RegisterForm

    template_name = "accounts_app/register.html"

    def dispatch(
            self,
            request,
            *args,
            **kwargs
    ):

        # کاربر لاگین شده نباید وارد Register شود
        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def form_valid(self, form):

        fullname = form.cleaned_data["fullname"]

        phone = form.cleaned_data["phone"]

        email = form.cleaned_data.get("email")

        password = form.cleaned_data["password1"]

        # ------------------------------------------
        # ایجاد OTP شش رقمی
        # ------------------------------------------

        code = f"{secrets.randbelow(1_000_000):06d}"

        # ------------------------------------------
        # حذف درخواست قبلی
        # ------------------------------------------

        RegistrationVerification.objects.filter(
            phone=phone
        ).delete()

        # ------------------------------------------
        # ایجاد Verification
        # ------------------------------------------

        verification = (
            RegistrationVerification.objects.create(

                fullname=fullname,

                phone=phone,

                email=email,

                password_hash=make_password(
                    password
                ),

                code_hash=make_password(
                    code
                ),

                expires_at=(
                        timezone.now()
                        + timedelta(
                    minutes=settings.MELIPAYAMAK_OTP_EXPIRE_MINUTES
                )
                ),

                attempts=0,

                last_sent_at=timezone.now(),
            )
        )

        # ------------------------------------------
        # ارسال SMS
        # ------------------------------------------

        try:

            send_otp_sms(
                phone=phone,
                code=code,
            )

        except Exception as error:

            verification.delete()

            form.add_error(
                None,
                f"ارسال کد تایید ناموفق بود: {error}"
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # ذخیره شماره در Session
        # ------------------------------------------

        self.request.session[
            "registration_phone"
        ] = phone

        # ------------------------------------------
        # انتقال به Verify
        # ------------------------------------------

        return redirect(
            "accounts_app:verify"
        )


# ==================================================
# Verify Registration
# ==================================================

class VerifyRegistrationView(FormView):
    template_name = "accounts_app/verify.html"

    form_class = OTPVerificationForm

    # ------------------------------------------
    # Access Control
    # ------------------------------------------

    def dispatch(
            self,
            request,
            *args,
            **kwargs
    ):

        # کاربر لاگین شده
        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        # دریافت شماره از Session
        phone = request.session.get(
            "registration_phone"
        )

        # Session وجود ندارد
        if not phone:
            return redirect(
                "accounts_app:register"
            )

        # بررسی Verification
        if not RegistrationVerification.objects.filter(
                phone=phone
        ).exists():
            request.session.pop(
                "registration_phone",
                None
            )

            return redirect(
                "accounts_app:register"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    # ------------------------------------------
    # Context
    # ------------------------------------------

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        phone = self.request.session.get(
            "registration_phone"
        )

        context["phone"] = phone

        try:

            verification = (
                RegistrationVerification.objects.get(
                    phone=phone
                )
            )

            now = timezone.now()

            remaining_seconds = int(
                (
                        verification.expires_at
                        - now
                ).total_seconds()
            )

            if remaining_seconds < 0:
                remaining_seconds = 0

            context["remaining_seconds"] = (
                remaining_seconds
            )

            context["can_resend"] = (
                    remaining_seconds <= 0
            )

        except RegistrationVerification.DoesNotExist:

            context["remaining_seconds"] = 0

            context["can_resend"] = True

        return context

    # ------------------------------------------
    # Verify OTP
    # ------------------------------------------

    def form_valid(self, form):

        phone = self.request.session.get(
            "registration_phone"
        )

        try:

            verification = (
                RegistrationVerification.objects.get(
                    phone=phone
                )
            )

        except RegistrationVerification.DoesNotExist:

            form.add_error(
                None,
                "درخواست ثبت نام پیدا نشد."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check expiration
        # ------------------------------------------

        if timezone.now() >= verification.expires_at:
            form.add_error(
                "code",
                "کد تایید منقضی شده است. لطفاً کد جدید درخواست کنید."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check attempts
        # ------------------------------------------

        if (
                verification.attempts
                >= settings.MELIPAYAMAK_MAX_OTP_ATTEMPTS
        ):
            form.add_error(
                None,
                "تعداد تلاش‌های شما بیش از حد مجاز است. لطفاً کد جدید درخواست کنید."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Get submitted OTP
        # ------------------------------------------

        code = form.cleaned_data["code"]

        # ------------------------------------------
        # Increase attempts
        # ------------------------------------------

        verification.attempts += 1

        verification.save(
            update_fields=[
                "attempts"
            ]
        )

        # ------------------------------------------
        # Check OTP
        # ------------------------------------------

        if not check_password(
                code,
                verification.code_hash
        ):
            form.add_error(
                "code",
                "کد تایید اشتباه است."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check phone duplicate
        # ------------------------------------------

        if User.objects.filter(
                phone=verification.phone
        ).exists():
            verification.delete()

            self.request.session.pop(
                "registration_phone",
                None
            )

            form.add_error(
                None,
                "این شماره قبلاً ثبت نام شده است."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check email duplicate
        # ------------------------------------------

        if (
                verification.email
                and User.objects.filter(
            email=verification.email
        ).exists()
        ):
            verification.delete()

            self.request.session.pop(
                "registration_phone",
                None
            )

            form.add_error(
                None,
                "این ایمیل قبلاً ثبت نام شده است."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Create final User
        # ------------------------------------------

        with transaction.atomic():

            User.objects.create(

                fullname=verification.fullname,

                phone=verification.phone,

                email=verification.email,

                password=verification.password_hash,

                is_active=True,
            )

            verification.delete()

        # ------------------------------------------
        # Clear registration session
        # ------------------------------------------

        self.request.session.pop(
            "registration_phone",
            None
        )

        # ------------------------------------------
        # Success message
        # ------------------------------------------

        messages.success(
            self.request,
            "ثبت نام با موفقیت انجام شد. اکنون وارد حساب خود شوید."
        )

        # ------------------------------------------
        # Login page
        # ------------------------------------------

        return redirect(
            "accounts_app:login"
        )


# ==================================================
# Resend OTP
# ==================================================

class ResendOTPView(View):

    def post(
            self,
            request,
            *args,
            **kwargs
    ):

        # ------------------------------------------
        # Logged-in user
        # ------------------------------------------

        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        # ------------------------------------------
        # Get phone from session
        # ------------------------------------------

        phone = request.session.get(
            "registration_phone"
        )

        if not phone:
            return redirect(
                "accounts_app:register"
            )

        # ------------------------------------------
        # Get verification
        # ------------------------------------------

        try:

            verification = (
                RegistrationVerification.objects.get(
                    phone=phone
                )
            )

        except RegistrationVerification.DoesNotExist:

            request.session.pop(
                "registration_phone",
                None
            )

            return redirect(
                "accounts_app:register"
            )

        # ------------------------------------------
        # Check expiration
        # ------------------------------------------

        now = timezone.now()

        if now < verification.expires_at:
            remaining = int(
                (
                        verification.expires_at
                        - now
                ).total_seconds()
            )

            messages.warning(
                request,
                f"لطفاً {remaining} ثانیه دیگر برای ارسال کد جدید صبر کنید."
            )

            return redirect(
                "accounts_app:verify"
            )

        # ------------------------------------------
        # Generate new OTP
        # ------------------------------------------

        code = f"{secrets.randbelow(1_000_000):06d}"

        # ------------------------------------------
        # Send new SMS
        # ------------------------------------------

        try:

            send_otp_sms(
                phone=phone,
                code=code,
            )

        except Exception as error:

            messages.error(
                request,
                f"ارسال مجدد کد ناموفق بود: {error}"
            )

            return redirect(
                "accounts_app:verify"
            )

        # ------------------------------------------
        # Replace old OTP
        # ------------------------------------------

        verification.code_hash = make_password(
            code
        )

        # ------------------------------------------
        # New 2-minute expiration
        # ------------------------------------------

        verification.expires_at = (
                timezone.now()
                + timedelta(
            minutes=settings.MELIPAYAMAK_OTP_EXPIRE_MINUTES
        )
        )

        # ------------------------------------------
        # Reset attempts
        # ------------------------------------------

        verification.attempts = 0

        # ------------------------------------------
        # Save send time
        # ------------------------------------------

        verification.last_sent_at = timezone.now()

        # ------------------------------------------
        # Save
        # ------------------------------------------

        verification.save(
            update_fields=[
                "code_hash",
                "expires_at",
                "attempts",
                "last_sent_at",
            ]
        )

        # ------------------------------------------
        # Success
        # ------------------------------------------

        messages.success(
            request,
            "کد تایید جدید برای شما ارسال شد."
        )

        return redirect(
            "accounts_app:verify"
        )


# ==================================================
# Forgot Password - Step 1
# ==================================================

class ForgotPasswordView(FormView):
    template_name = "accounts_app/forgot_password.html"

    form_class = ForgotPasswordPhoneForm

    def dispatch(
            self,
            request,
            *args,
            **kwargs
    ):

        # کاربر لاگین شده نیازی به بازیابی رمز ندارد
        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def form_valid(self, form):

        phone = form.cleaned_data["phone"]

        # ------------------------------------------
        # پیدا کردن کاربر
        # ------------------------------------------

        user = User.objects.filter(
            phone=phone,
            is_active=True
        ).first()

        # ------------------------------------------
        # پیام عمومی
        # ------------------------------------------

        # عمداً در صورت وجود نداشتن شماره،
        # نمی‌گوییم چنین کاربری وجود ندارد.
        #
        # این کار از User Enumeration جلوگیری می‌کند.

        if not user:
            messages.success(
                self.request,
                "اگر این شماره در سیستم ثبت شده باشد، کد تایید برای آن ارسال خواهد شد."
            )

            return redirect(
                "accounts_app:login"
            )

        # ------------------------------------------
        # حذف درخواست قبلی
        # ------------------------------------------

        PasswordResetVerification.objects.filter(
            phone=phone
        ).delete()

        # ------------------------------------------
        # Generate OTP
        # ------------------------------------------

        code = f"{secrets.randbelow(1_000_000):06d}"

        # ------------------------------------------
        # Create verification
        # ------------------------------------------

        verification = (
            PasswordResetVerification.objects.create(

                phone=phone,

                code_hash=make_password(
                    code
                ),

                expires_at=(
                        timezone.now()
                        + timedelta(
                    minutes=settings.MELIPAYAMAK_OTP_EXPIRE_MINUTES
                )
                ),

                attempts=0,

                last_sent_at=timezone.now(),
            )
        )

        # ------------------------------------------
        # Send SMS
        # ------------------------------------------

        try:

            send_otp_sms(
                phone=phone,
                code=code,
            )

        except Exception:

            verification.delete()

            form.add_error(
                None,
                "ارسال کد تایید ناموفق بود. لطفاً دوباره تلاش کنید."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Save phone in session
        # ------------------------------------------

        self.request.session[
            "password_reset_phone"
        ] = phone

        # ------------------------------------------
        # Redirect
        # ------------------------------------------

        return redirect(
            "accounts_app:forgot_password_verify"
        )


# ==================================================
# Forgot Password - Step 2
# Verify OTP
# ==================================================

class ForgotPasswordVerifyView(FormView):
    template_name = (
        "accounts_app/forgot_password_verify.html"
    )

    form_class = ForgotPasswordOTPForm

    def dispatch(
            self,
            request,
            *args,
            **kwargs
    ):

        # کاربر لاگین شده
        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        phone = request.session.get(
            "password_reset_phone"
        )

        if not phone:
            return redirect(
                "accounts_app:forgot_password"
            )

        if not PasswordResetVerification.objects.filter(
                phone=phone
        ).exists():
            request.session.pop(
                "password_reset_phone",
                None
            )

            return redirect(
                "accounts_app:forgot_password"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        phone = self.request.session.get(
            "password_reset_phone"
        )

        context["phone"] = phone

        try:

            verification = (
                PasswordResetVerification.objects.get(
                    phone=phone
                )
            )

            remaining_seconds = int(
                (
                        verification.expires_at
                        - timezone.now()
                ).total_seconds()
            )

            if remaining_seconds < 0:
                remaining_seconds = 0

            context[
                "remaining_seconds"
            ] = remaining_seconds

            context[
                "can_resend"
            ] = remaining_seconds <= 0

        except PasswordResetVerification.DoesNotExist:

            context["remaining_seconds"] = 0

            context["can_resend"] = True

        return context

    def form_valid(self, form):

        phone = self.request.session.get(
            "password_reset_phone"
        )

        try:

            verification = (
                PasswordResetVerification.objects.get(
                    phone=phone
                )
            )

        except PasswordResetVerification.DoesNotExist:

            form.add_error(
                None,
                "درخواست بازیابی رمز پیدا نشد."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check expiration
        # ------------------------------------------

        if timezone.now() >= verification.expires_at:
            form.add_error(
                "code",
                "کد تایید منقضی شده است. لطفاً کد جدید درخواست کنید."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Check attempts
        # ------------------------------------------

        if (
                verification.attempts
                >= settings.MELIPAYAMAK_MAX_OTP_ATTEMPTS
        ):
            form.add_error(
                None,
                "تعداد تلاش‌های شما بیش از حد مجاز است. لطفاً کد جدید درخواست کنید."
            )

            return self.form_invalid(form)

        code = form.cleaned_data["code"]

        # ------------------------------------------
        # Increase attempts
        # ------------------------------------------

        verification.attempts += 1

        verification.save(
            update_fields=[
                "attempts"
            ]
        )

        # ------------------------------------------
        # Check OTP
        # ------------------------------------------

        if not check_password(
                code,
                verification.code_hash
        ):
            form.add_error(
                "code",
                "کد تایید اشتباه است."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # OTP verified
        # ------------------------------------------

        self.request.session[
            "password_reset_verified"
        ] = True

        return redirect(
            "accounts_app:reset_password"
        )


# ==================================================
# Forgot Password - Step 3
# Reset Password
# ==================================================

class ResetPasswordView(FormView):
    template_name = (
        "accounts_app/reset_password.html"
    )

    form_class = ResetPasswordForm

    def dispatch(
            self,
            request,
            *args,
            **kwargs
    ):

        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        phone = request.session.get(
            "password_reset_phone"
        )

        verified = request.session.get(
            "password_reset_verified"
        )

        if not phone or not verified:
            return redirect(
                "accounts_app:forgot_password"
            )

        if not User.objects.filter(
                phone=phone,
                is_active=True
        ).exists():
            request.session.pop(
                "password_reset_phone",
                None
            )

            request.session.pop(
                "password_reset_verified",
                None
            )

            return redirect(
                "accounts_app:forgot_password"
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        phone = self.request.session.get(
            "password_reset_phone"
        )

        user = User.objects.get(
            phone=phone
        )

        kwargs["user"] = user

        return kwargs

    def form_valid(self, form):

        phone = self.request.session.get(
            "password_reset_phone"
        )

        try:

            user = User.objects.get(
                phone=phone,
                is_active=True
            )

        except User.DoesNotExist:

            form.add_error(
                None,
                "کاربر پیدا نشد."
            )

            return self.form_invalid(form)

        # ------------------------------------------
        # Set new password
        # ------------------------------------------

        user.set_password(
            form.cleaned_data["password1"]
        )

        user.save(
            update_fields=[
                "password"
            ]
        )

        # ------------------------------------------
        # Delete OTP verification
        # ------------------------------------------

        PasswordResetVerification.objects.filter(
            phone=phone
        ).delete()

        # ------------------------------------------
        # Clear session
        # ------------------------------------------

        self.request.session.pop(
            "password_reset_phone",
            None
        )

        self.request.session.pop(
            "password_reset_verified",
            None
        )

        # ------------------------------------------
        # Login automatically
        # ------------------------------------------

        from django.contrib.auth import login

        login(
            self.request,
            user
        )

        # ------------------------------------------
        # Success
        # ------------------------------------------

        messages.success(
            self.request,
            "رمز عبور شما با موفقیت تغییر کرد."
        )

        return redirect(
            "home_app:home"
        )


# ==================================================
# Forgot Password - Resend OTP
# ==================================================

class ResendPasswordResetOTPView(View):

    def post(
            self,
            request,
            *args,
            **kwargs
    ):

        # ------------------------------------------
        # Logged in user
        # ------------------------------------------

        if request.user.is_authenticated:
            return redirect(
                "home_app:home"
            )

        # ------------------------------------------
        # Get phone
        # ------------------------------------------

        phone = request.session.get(
            "password_reset_phone"
        )

        if not phone:
            return redirect(
                "accounts_app:forgot_password"
            )

        # ------------------------------------------
        # Get verification
        # ------------------------------------------

        try:

            verification = (
                PasswordResetVerification.objects.get(
                    phone=phone
                )
            )

        except PasswordResetVerification.DoesNotExist:

            request.session.pop(
                "password_reset_phone",
                None
            )

            return redirect(
                "accounts_app:forgot_password"
            )

        # ------------------------------------------
        # Check cooldown
        # ------------------------------------------

        now = timezone.now()

        if now < verification.expires_at:
            remaining = int(
                (
                        verification.expires_at
                        - now
                ).total_seconds()
            )

            messages.warning(
                request,
                f"لطفاً {remaining} ثانیه دیگر صبر کنید."
            )

            return redirect(
                "accounts_app:forgot_password_verify"
            )

        # ------------------------------------------
        # Generate new OTP
        # ------------------------------------------

        code = f"{secrets.randbelow(1_000_000):06d}"

        # ------------------------------------------
        # Send SMS
        # ------------------------------------------

        try:

            send_otp_sms(
                phone=phone,
                code=code,
            )

        except Exception:

            messages.error(
                request,
                "ارسال کد جدید ناموفق بود. لطفاً دوباره تلاش کنید."
            )

            return redirect(
                "accounts_app:forgot_password_verify"
            )

        # ------------------------------------------
        # Replace old OTP
        # ------------------------------------------

        verification.code_hash = make_password(
            code
        )

        verification.expires_at = (
                timezone.now()
                + timedelta(
            minutes=settings.MELIPAYAMAK_OTP_EXPIRE_MINUTES
        )
        )

        verification.attempts = 0

        verification.last_sent_at = timezone.now()

        verification.save(
            update_fields=[
                "code_hash",
                "expires_at",
                "attempts",
                "last_sent_at",
            ]
        )

        messages.success(
            request,
            "کد تایید جدید برای شما ارسال شد."
        )

        return redirect(
            "accounts_app:forgot_password_verify"
        )


class UserLogout(View):

    def post(self, request):
        logout(request)

        return redirect("home_app:home")
