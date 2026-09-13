from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

User = get_user_model()

# ==================================================
# Phone Validator
# ==================================================

phone_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="شماره تلفن باید 11 رقم و با 09 شروع شود."
)


# ==================================================
# Login Form
# ==================================================

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Phone Number",
        validators=[
            phone_validator
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone Number",
                "maxlength": "11",
                "autocomplete": "tel",
                "inputmode": "tel",
            }
        )
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )


# ==================================================
# Register Form
# ==================================================

class RegisterForm(UserCreationForm):
    fullname = forms.CharField(
        label="Full Name",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Full Name",
                "autocomplete": "name",
            }
        )
    )

    phone = forms.CharField(
        label="Phone Number",
        validators=[
            phone_validator
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone Number",
                "maxlength": "11",
                "autocomplete": "tel",
                "inputmode": "tel",
            }
        )
    )

    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "autocomplete": "email",
            }
        )
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "new-password",
            }
        )
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
                "autocomplete": "new-password",
            }
        )
    )

    class Meta:

        model = User

        fields = (
            "fullname",
            "phone",
            "email",
            "password1",
            "password2",
        )

    def clean_phone(self):

        phone = self.cleaned_data["phone"]

        if User.objects.filter(
                phone=phone
        ).exists():
            raise ValidationError(
                "این شماره تلفن قبلاً ثبت نام کرده است."
            )

        return phone

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if email and User.objects.filter(
                email=email
        ).exists():
            raise ValidationError(
                "این ایمیل قبلاً ثبت نام کرده است."
            )

        return email


# ==================================================
# OTP Verification Form
# ==================================================

class OTPVerificationForm(forms.Form):
    code = forms.CharField(
        label="Verification Code",
        max_length=6,
        min_length=6,
        validators=[
            RegexValidator(
                regex=r"^\d{6}$",
                message="کد تایید باید 6 رقم باشد."
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "Verification Code",
                "maxlength": "6",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        )
    )
