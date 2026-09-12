# # from django import forms
# # from django.contrib.auth.forms import AuthenticationForm
# # from django.core import validators
# #
# #
# # class LoginForm(AuthenticationForm):
# #     username = forms.CharField(
# #         label='Phone Number',
# #         widget=forms.TextInput(
# #             attrs={
# #                 'class': 'form-control',
# #                 'placeholder': 'Phone Number',
# #             }
# #         ),
# #         validators=[validators.MaxLengthValidator(11)],
# #     )
# #
# #     password = forms.CharField(
# #         label='Password',
# #         widget=forms.PasswordInput(
# #             attrs={
# #                 'class': 'form-control',
# #                 'placeholder': 'Password',
# #             }
# #         ),
# #     )
#
# from django import forms
# from django.contrib.auth import authenticate, get_user_model
# from django.contrib.auth.forms import AuthenticationForm
# from django.core.exceptions import ValidationError
# from django.core.validators import RegexValidator
#
# User = get_user_model()
#
#
# class LoginForm(AuthenticationForm):
#     username = forms.CharField(
#         label='Phone Number',
#         validators=[
#             RegexValidator(
#                 regex=r'^09\d{9}$',
#                 message='شماره تلفن باید 11 رقم و با 09 شروع شود'
#             )
#         ],
#         widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Phone Number',
#                 'maxlength': '11',
#             }
#         )
#     )
#
#     password = forms.CharField(
#         label='Password',
#         widget=forms.PasswordInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Password',
#             }
#         )
#     )
#
#     def clean(self):
#         phone = self.cleaned_data.get('username')
#         password = self.cleaned_data.get('password')
#
#         if phone and password:
#
#             # بررسی وجود شماره تلفن
#             try:
#                 user = User.objects.get(phone=phone)
#             except User.DoesNotExist:
#                 raise ValidationError(
#                     'شماره تلفن وارد شده اشتباه است'
#                 )
#
#             # بررسی رمز عبور
#             if not user.check_password(password):
#                 raise ValidationError(
#                     'رمز عبور وارد شده اشتباه است'
#                 )
#
#             # بررسی فعال بودن کاربر
#             if not user.is_active:
#                 raise ValidationError(
#                     'حساب کاربری شما غیرفعال است'
#                 )
#
#             # احراز هویت
#             self.user_cache = authenticate(
#                 self.request,
#                 phone=phone,
#                 password=password,
#             )
#
#             if self.user_cache is None:
#                 raise ValidationError(
#                     'ورود به حساب کاربری امکان‌پذیر نیست'
#                 )
#
#         return self.cleaned_data
#
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='شماره تلفن',
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره تلفن باید ۱۱ رقم و با ۰۹ شروع شود'
            )
        ],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '09123456789',
                'maxlength': '11',
                'dir': 'ltr',
            }
        )
    )

    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'رمز عبور',
                'id': 'id_password',
            }
        )
    )

    error_messages = {
        'invalid_login': 'شماره تلفن یا رمز عبور اشتباه است.',
        'inactive': 'حساب کاربری شما غیرفعال است.',
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )

            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class PhoneForm(forms.Form):
    phone = forms.CharField(
        label='شماره تلفن',
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره تلفن باید ۱۱ رقم و با ۰۹ شروع شود'
            )
        ],
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '09123456789',
                'dir': 'ltr',
                'maxlength': '11',
            }
        )
    )


class VerifyOTPForm(forms.Form):
    code = forms.CharField(
        label='کد تأیید',
        max_length=6,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'کد ۶ رقمی',
                'dir': 'ltr',
                'autocomplete': 'one-time-code',
                'maxlength': '6',
            }
        )
    )
