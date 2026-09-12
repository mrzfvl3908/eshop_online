from melipayamak import Api
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MelipayamakService:
    def __init__(self):
        self.username = settings.MELIPAYAMAK_USERNAME
        self.api_key = settings.MELIPAYAMAK_API_KEY
        self.from_number = settings.MELIPAYAMAK_FROM_NUMBER

        self.api = Api(self.username, self.api_key)
        self.sms = self.api.sms()

    def send_simple(self, to: str, text: str, is_flash: bool = False) -> dict:
        try:
            response = self.sms.send(to, self.from_number, text, is_flash)

            if response.get('RetStatus') == 1:
                logger.info(f"پیامک با موفقیت ارسال شد. recId: {response.get('Value')}")
            else:
                logger.error(f"خطا در ارسال پیامک: {response}")

            return response
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در ارسال پیامک: {str(e)}")
            return {'Value': None, 'RetStatus': -1, 'StrRetStatus': str(e)}

    def is_delivered(self, rec_id: str) -> dict:
        try:
            return self.sms.is_delivered(rec_id)
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت تحویل: {str(e)}")
            return {'error': str(e)}

    def get_credit(self) -> dict:
        try:
            return self.sms.get_credit()
        except Exception as e:
            logger.error(f"خطا در دریافت موجودی: {str(e)}")
            return {'error': str(e)}


# نمونه آماده برای استفاده
sms_service = MelipayamakService()
