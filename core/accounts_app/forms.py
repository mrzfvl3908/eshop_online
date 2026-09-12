# from django import forms
# from django.contrib.auth.forms import AuthenticationForm
# from django.core import validators
#
#
# class LoginForm(AuthenticationForm):
#     username = forms.CharField(
#         label='Phone Number',
#         widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Phone Number',
#             }
#         ),
#         validators=[validators.MaxLengthValidator(11)],
#     )
#
#     password = forms.CharField(
#         label='Password',
#         widget=forms.PasswordInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Password',
#             }
#         ),
#     )

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Phone Number',
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره تلفن باید 11 رقم و با 09 شروع شود'
            )
        ],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'maxlength': '11',
            }
        )
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password',
            }
        )
    )

    def clean(self):
        phone = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if phone and password:

            # بررسی وجود شماره تلفن
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                raise ValidationError(
                    'شماره تلفن وارد شده اشتباه است'
                )

            # بررسی رمز عبور
            if not user.check_password(password):
                raise ValidationError(
                    'رمز عبور وارد شده اشتباه است'
                )

            # بررسی فعال بودن کاربر
            if not user.is_active:
                raise ValidationError(
                    'حساب کاربری شما غیرفعال است'
                )

            # احراز هویت
            self.user_cache = authenticate(
                self.request,
                phone=phone,
                password=password,
            )

            if self.user_cache is None:
                raise ValidationError(
                    'ورود به حساب کاربری امکان‌پذیر نیست'
                )

        return self.cleaned_data

