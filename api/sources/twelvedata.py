from __future__ import annotations
from typing import Any
from api.client import HttpClient
from core.candle import Candle
from core.config import Config
from core.exceptions import APIError, ValidationError
from core.logger import logger


class TwelveDataSource:
    """
    يتولى الاتصال بواجهة TwelveData API وتحويل الردود إلى كائنات Candle.
    """

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(
        self, http_client: HttpClient | None = None, api_key: str | None = None
    ) -> None:
        self.http_client = http_client or HttpClient()
        # قراءة المفتاح من الإعدادات أو استخدام 'demo' كقيمة تجريبية
        config = Config()
        self.api_key = api_key or config.get("twelvedata_api_key", "demo")

    def fetch_candles(
        self, pair: str = "EUR/USD", interval: str = "1day", limit: int = 1
    ) -> list[Candle]:
        """
        جلب سلسلة الشموع السعرية لزوج معين وتحويلها إلى قائمة من كائنات Candle.
        """
        params: dict[str, Any] = {
            "symbol": pair,
            "interval": interval,
            "outputsize": limit,
            "apikey": self.api_key,
        }

        logger.info(f"جلب الشموع لزوج {pair} من TwelveData (العدد: {limit})...")
        raw_response = self.http_client.get(self.BASE_URL, params=params)

        # التحقق من أخطاء الـ API (TwelveData يرجع status: error داخل الـ JSON)
        if raw_response.get("status") == "error":
            error_message = raw_response.get("message", "خطأ غير معروف من TwelveData")
            logger.error(f"فشل استدعاء TwelveData: {error_message}")
            raise APIError(f"TwelveData API Error: {error_message}")

        values = raw_response.get("values", [])
        if not values:
            logger.warning(f"لم يتم العثور على شموع لزوج {pair}.")
            return []

        candles: list[Candle] = []
        for item in values:
            # دمج اسم الزوج لأن الـ API يرجعه في الـ meta وليس داخل كل شمعة
            item["symbol"] = pair
            try:
                candle = Candle.from_dict(item)
                candles.append(candle)
            except ValidationError as err:
                logger.warning(f"تجاهل شمعة غير صالحة بسبب خطأ تحقق: {err}")

        logger.info(f"تم بنجاح تحويل {len(candles)} شمعة إلى كائنات Candle.")
        return candles
