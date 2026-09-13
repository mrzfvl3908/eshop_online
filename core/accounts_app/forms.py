from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

phone_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="شماره تلفن باید 11 رقم و با 09 شروع شود"
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Phone Number",
        validators=[phone_validator],
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

    remember_me = forms.BooleanField(
        label="Remember me",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input"
            }
        )
    )


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
        max_length=11,
        validators=[phone_validator],
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

        phone = self.cleaned_data["phone"].strip()

        if User.objects.filter(phone=phone).exists():
            raise ValidationError(
                "این شماره تلفن قبلاً ثبت نام کرده است."
            )

        return phone

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

            if User.objects.filter(email=email).exists():
                raise ValidationError(
                    "این ایمیل قبلاً ثبت نام کرده است."
                )

        return email


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


class ForgotPasswordPhoneForm(forms.Form):
    phone = forms.CharField(
        label="Phone Number",
        max_length=11,
        validators=[phone_validator],
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


class ForgotPasswordOTPForm(forms.Form):
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


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New Password",
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

    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.user = user

    def clean_password1(self):

        password1 = self.cleaned_data.get("password1")

        if self.user and password1:
            validate_password(
                password1,
                self.user
            )

        return password1

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if (
                password1
                and password2
                and password1 != password2
        ):
            raise ValidationError(
                "رمزهای عبور یکسان نیستند."
            )

        return cleaned_data
