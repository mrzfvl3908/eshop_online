from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from accounts_app.models import User


# =========================================================
# فرم ساخت کاربر جدید در پنل Admin
# =========================================================

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="گذرواژه",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="تکرار گذرواژه",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = [
            "phone",
            "fullname",
            "email",
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("گذرواژه‌ها یکسان نیستند.")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)

        # رمز عبور را Hash می‌کنیم
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


# =========================================================
# فرم ویرایش کاربر در Admin
# =========================================================

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="گذرواژه"
    )

    class Meta:
        model = User
        fields = [
            "phone",
            "fullname",
            "email",
            "password",
            "is_active",
            "is_admin",
        ]


# =========================================================
# تنظیمات User در Admin
# =========================================================

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = [
        "phone",
        "fullname",
        "email",
        "is_admin",
        "is_active",
    ]

    list_filter = [
        "is_admin",
        "is_active",
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "phone",
                    "password",
                ]
            },
        ),

        (
            "اطلاعات شخصی",
            {
                "fields": [
                    "fullname",
                    "email",
                ]
            },
        ),

        (
            "دسترسی‌ها",
            {
                "fields": [
                    "is_admin",
                    "is_active",
                ]
            },
        ),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "phone",
                    "fullname",
                    "email",
                    "password1",
                    "password2",
                ],
            },
        ),
    ]

    search_fields = [
        "phone",
        "fullname",
        "email",
    ]

    ordering = [
        "phone",
    ]

    filter_horizontal = []


# =========================================================
# ثبت User در Admin
# =========================================================

admin.site.register(User, UserAdmin)

# چون از سیستم Permission/Group پیش‌فرض Django استفاده نمی‌کنیم
admin.site.unregister(Group)
