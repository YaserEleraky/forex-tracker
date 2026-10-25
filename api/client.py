from __future__ import annotations
from typing import Any
import requests
from core.exceptions import NetworkError
from core.logger import logger


class HttpClient:
    """
    عميل HTTP يغلف مكتبة requests لتطبيق معايير موحدة للـ Timeout ومعالجة الاستثناءات.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._session = requests.Session()

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        إرسال طلب GET وإرجاع البيانات كـ JSON مع معالجة أخطاء الاتصال.
        """
        try:
            logger.info(f"إرسال طلب HTTP GET إلى: {url}")
            response = self._session.get(url, params=params, timeout=self.timeout)

            # التحقق من أن كود الاستجابة ناجح (200-299)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.Timeout as err:
            logger.error(f"انتهت مهلة الاتصال بالخادم ({self.timeout} ثوانٍ): {url}")
            raise NetworkError(f"انتهت مهلة الاتصال: {err}") from err

        except requests.ConnectionError as err:
            logger.error(f"تعذر الاتصال بالخادم، تحقق من الإنترنت: {url}")
            raise NetworkError(f"فشل الاتصال بالشبكة: {err}") from err

        except requests.HTTPError as err:
            status_code = response.status_code if "response" in locals() else "Unknown"
            logger.error(f"أرجع الخادم خطأ HTTP {status_code}: {url}")
            raise NetworkError(f"خطأ HTTP من الخادم ({status_code}): {err}") from err

        except requests.RequestException as err:
            logger.error(f"حدث خطأ غير متوقع أثناء طلب HTTP: {err}")
            raise NetworkError(f"خطأ عام في الشبكة: {err}") from err
