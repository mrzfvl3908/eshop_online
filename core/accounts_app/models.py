from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")

        user = self.model(
            phone=phone,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        return user

    def create_superuser(self, phone, password=None, **extra_fields):

        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_admin") is not True:
            raise ValueError("Superuser must have is_admin=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            phone=phone,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
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

    @property
    def is_staff(self):
        return self.is_admin


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

    password_hash = models.CharField(
        max_length=255,
        verbose_name="رمز عبور هش شده"
    )

    code_hash = models.CharField(
        max_length=255,
        verbose_name="کد تایید هش شده"
    )

    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا"
    )

    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تلاش"
    )

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
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return self.phone

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class PasswordResetVerification(models.Model):
    phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره تلفن"
    )

    code_hash = models.CharField(
        max_length=255,
        verbose_name="کد تایید هش شده"
    )

    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا"
    )

    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تلاش"
    )

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
        verbose_name = "بازیابی رمز عبور"
        verbose_name_plural = "بازیابی‌های رمز عبور"
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return self.phone

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
