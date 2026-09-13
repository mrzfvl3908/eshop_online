from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone


# ==================================================
# User Manager
# ==================================================

class UserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError(
                "Users must have a phone number"
            )

        user = self.model(
            phone=phone,
            **extra_fields
        )

        user.set_password(password)

        user.save(
            using=self._db
        )

        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        user = self.create_user(
            phone=phone,
            password=password,
            **extra_fields
        )

        user.is_admin = True
        user.is_active = True

        user.save(
            using=self._db
        )

        return user


# ==================================================
# User
# ==================================================

class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="ایمیل",
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    fullname = models.CharField(
        max_length=255,
        verbose_name="نام کامل"
    )

    phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره تلفن"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    is_admin = models.BooleanField(
        default=False,
        verbose_name="ادمین"
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"

        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin


# ==================================================
# Registration Verification
# ==================================================

class RegistrationVerification(models.Model):
    fullname = models.CharField(
        max_length=255,
        verbose_name="نام کامل"
    )

    phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره تلفن"
    )

    email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="ایمیل"
    )

    # رمز عبور کاربر قبل از تکمیل ثبت نام
    password_hash = models.CharField(
        max_length=255,
        verbose_name="رمز عبور هش شده"
    )

    # OTP به صورت Hash ذخیره می‌شود
    code_hash = models.CharField(
        max_length=255,
        verbose_name="کد تایید هش شده"
    )

    # زمان انقضای OTP
    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا"
    )

    # تعداد تلاش برای وارد کردن OTP
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تلاش"
    )

    # آخرین زمان ارسال OTP
    last_sent_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="آخرین ارسال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "تایید ثبت نام"

        verbose_name_plural = "تاییدهای ثبت نام"

    def __str__(self):
        return self.phone

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
