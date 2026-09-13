import requests

from django.conf import settings
from django.core.exceptions import ValidationError


def send_otp_sms(phone, code):
    data = {
        "bodyId": settings.MELIPAYAMAK_BODY_ID,
        "to": phone,
        "args": [
            code
        ],
    }

    try:

        response = requests.post(
            settings.MELIPAYAMAK_SHARED_URL,
            json=data,
            timeout=15,
        )

        response.raise_for_status()

        result = response.json()

    except requests.RequestException:

        raise ValidationError(
            "ارتباط با سرویس پیامک برقرار نشد."
        )

    except ValueError:

        raise ValidationError(
            "پاسخ نامعتبر از سرویس پیامک دریافت شد."
        )

    # ------------------------------------------
    # Melipayamak successful response
    # ------------------------------------------

    if result.get("recId"):
        return result

    # ------------------------------------------
    # SMS provider error
    # ------------------------------------------

    status = result.get("status")

    if status:
        raise ValidationError(
            f"خطا در ارسال پیامک: {status}"
        )

    raise ValidationError(
        "ارسال پیامک توسط سرویس تایید نشد."
    )
