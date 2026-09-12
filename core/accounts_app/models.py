# from django.db import models
# from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
#
#
# # اگر خواستی از ایمیل استفاده کنی جای تلفن همرو باید ایمیل بزاری و در ادمین هم همینطور
# class UserManager(BaseUserManager):
#     def create_user(self, phone, password=None):
#         """
#         Creates and saves a User with the given email and password.
#         """
#         if not phone:
#             raise ValueError("Users must have an phone number")
#
#         user = self.model(
#             phone=phone,
#             # email = self.normalize_email(email)
#         )
#
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, phone, password=None):
#         """
#         Creates and saves a superuser with the given phone and password.
#         """
#         user = self.create_user(
#             phone,
#             password=password,
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user
#
#
# class User(AbstractBaseUser):
#     email = models.EmailField(
#         verbose_name="ایمیل",
#         max_length=255,
#         unique=True,
#         null=True,
#         blank=True,
#     )
#     fullname = models.CharField(max_length=255, verbose_name='نام کامل')
#     phone = models.CharField(max_length=12, unique=True, verbose_name='شماره تلفن')
#     is_active = models.BooleanField(default=True, verbose_name='فعال')
#     is_admin = models.BooleanField(default=False, verbose_name='ادمین')
#
#     objects = UserManager()
#
#     USERNAME_FIELD = "phone"
#     REQUIRED_FIELDS = []
#
#     class Meta:
#         verbose_name = 'کاربر'
#         verbose_name_plural = 'کاربران'
#
#     def __str__(self):
#         return self.phone
#
#     def has_perm(self, perm, obj=None):
#         "Does the user have a specific permission?"
#         # Simplest possible answer: Yes, always
#         return True
#
#     def has_module_perms(self, app_label):
#         "Does the user have permissions to view the app `app_label`?"
#         # Simplest possible answer: Yes, always
#         return True
#
#     @property
#     def is_staff(self):
#         "Is the user a member of staff?"
#         # Simplest possible answer: All admins are staff
#         return self.is_admin

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
import random


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError("Users must have a phone number")

        user = self.model(phone=phone)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None):
        user = self.create_user(phone, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="ایمیل",
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    fullname = models.CharField(max_length=255, verbose_name='نام کامل', null=True, blank=True)
    phone = models.CharField(max_length=12, unique=True, verbose_name='شماره تلفن')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_admin = models.BooleanField(default=False, verbose_name='ادمین')

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class OTPCode(models.Model):
    phone = models.CharField(max_length=12, verbose_name='شماره تلفن')
    code = models.CharField(max_length=6, verbose_name='کد تأیید')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')

    class Meta:
        verbose_name = 'کد یکبار مصرف'
        verbose_name_plural = 'کدهای یکبار مصرف'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone} - {self.code}"

    def is_expired(self):
        """کد بعد از ۲ دقیقه منقضی می‌شود"""
        return timezone.now() > self.created_at + timezone.timedelta(minutes=2)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))
