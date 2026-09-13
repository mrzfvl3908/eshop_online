import secrets
from datetime import timedelta
from django.contrib.auth import logout
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import (
    make_password,
    check_password,
)
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    FormView,
    View,
)

from .forms import (
    LoginForm,
    RegisterForm,
    OTPVerificationForm,
)

from .models import (
    User,
    RegistrationVerification,
)

from .sms import send_otp_sms


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


class UserLogout(View):

    def post(self, request):
        logout(request)

        return redirect("home_app:home")
