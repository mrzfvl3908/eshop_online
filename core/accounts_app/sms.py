import logging

import requests

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def send_otp_sms(phone, code):
    data = {
        "bodyId": settings.MELIPAYAMAK_BODY_ID,
        "to": phone,
        "args": [code],
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

        logger.exception(
            "SMS provider request failed."
        )

        raise ValidationError(
            "ارسال پیامک انجام نشد. لطفاً دوباره تلاش کنید."
        )

    except ValueError:

        logger.exception(
            "Invalid response from SMS provider."
        )

        raise ValidationError(
            "ارسال پیامک انجام نشد. لطفاً دوباره تلاش کنید."
        )

    if result.get("recId"):
        return result

    logger.error(
        "SMS provider rejected OTP request. Response: %s",
        result,
    )

    raise ValidationError(
        "ارسال پیامک انجام نشد. لطفاً دوباره تلاش کنید."
    )
