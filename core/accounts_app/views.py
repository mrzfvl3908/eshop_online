# from django.contrib.auth.views import LoginView
# from .forms import LoginForm
#
#
# class UserLogin(LoginView):
#     template_name = 'accounts_app/login.html'
#     authentication_form = LoginForm
#     redirect_authenticated_user = True

from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from .forms import LoginForm, PhoneForm, VerifyOTPForm
from .models import User, OTPCode
from services.sms import sms_service


class UserLogin(LoginView):
    template_name = 'accounts_app/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class OTPLoginView(View):
    template_name = 'accounts_app/otp_login.html'

    def get(self, request):
        # اگر کاربر قبلاً لاگین کرده باشد
        if request.user.is_authenticated:
            return redirect('home_app:home')

        return render(request, self.template_name)

    def post(self, request):
        action = request.POST.get('action')

        # ========== مرحله ۱: ارسال کد ==========
        if action == 'send_code':
            phone = request.POST.get('phone', '').strip()

            # اعتبارسنجی شماره
            if not phone or len(phone) != 11 or not phone.startswith('09'):
                return JsonResponse({
                    'success': False,
                    'message': 'شماره تلفن باید ۱۱ رقم و با ۰۹ شروع شود.'
                })

            # حذف کدهای قبلی
            OTPCode.objects.filter(phone=phone, is_used=False).delete()

            # ساخت کد جدید
            code = OTPCode.generate_code()
            OTPCode.objects.create(phone=phone, code=code)

            # ارسال پیامک
            text = f"کد تأیید شما: {code}\nاین کد تا ۲ دقیقه معتبر است."
            response = sms_service.send_simple(to=phone, text=text)

            if response.get('RetStatus') == 1:
                request.session['otp_phone'] = phone
                return JsonResponse({
                    'success': True,
                    'message': 'کد تأیید با موفقیت ارسال شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در ارسال پیامک. لطفاً دوباره تلاش کنید.'
                })

        # ========== مرحله ۲: تأیید کد و ورود ==========
        elif action == 'verify_code':
            phone = request.session.get('otp_phone')
            code = request.POST.get('code', '').strip()

            if not phone:
                return JsonResponse({
                    'success': False,
                    'message': 'جلسه منقضی شده. لطفاً دوباره شماره را وارد کنید.'
                })

            if not code or len(code) != 6:
                return JsonResponse({
                    'success': False,
                    'message': 'کد تأیید باید ۶ رقم باشد.'
                })

            try:
                otp = OTPCode.objects.get(
                    phone=phone,
                    code=code,
                    is_used=False
                )

                if otp.is_expired():
                    return JsonResponse({
                        'success': False,
                        'message': 'کد منقضی شده است. لطفاً دوباره درخواست دهید.'
                    })

                # کد صحیح است
                otp.is_used = True
                otp.save()
                
                # کاربر را پیدا کن یا بساز
                user, created = User.objects.get_or_create(phone=phone)

                login(request, user)
                del request.session['otp_phone']

                return JsonResponse({
                    'success': True,
                    'message': 'ورود با موفقیت انجام شد.',
                    'redirect_url': '/'  # آدرس صفحه اصلی
                })

            except OTPCode.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'کد وارد شده اشتباه است.'
                })

        return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})
