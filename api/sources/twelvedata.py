from __future__ import annotations
from typing import Any
from api.client import HttpClient
from core.candle import Candle
from core.config import Config
from core.exceptions import APIError, ValidationError
from core.logger import logger


class TwelveDataSource:
    """يتولى الاتصال بـ TwelveData وتحويل الردود إلى كائنات Candle."""

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(
        self, http_client: HttpClient | None = None, api_key: str | None = None
    ) -> None:
        self.http_client = http_client or HttpClient()
        config = Config()
        self.api_key = api_key or config.get("twelvedata_api_key", "demo")

    def fetch_candles(
        self, pair: str = "EUR/USD", interval: str = "1day", limit: int = 1
    ) -> list[Candle]:
        """
        جلب سلسلة الشموع السعرية لزوج معين بإطار زمني محدد.
        """
        params: dict[str, Any] = {
            "symbol": pair,
            "interval": interval,
            "outputsize": limit,
            "apikey": self.api_key,
        }

        logger.info(f"جلب {limit} شمعة لزوج {pair} بإطار {interval} من TwelveData...")
        raw_response = self.http_client.get(self.BASE_URL, params=params)

        if raw_response.get("status") == "error":
            error_message = raw_response.get("message", "خطأ غير معروف من TwelveData")
            logger.error(f"فشل طلب TwelveData: {error_message}")
            raise APIError(f"TwelveData API Error: {error_message}")

        values = raw_response.get("values", [])
        if not values:
            logger.warning(f"لم ترجع أي شموع لزوج {pair} بالإطار {interval}.")
            return []

        candles: list[Candle] = []
        for item in values:
            item["symbol"] = pair
            item["interval"] = interval
            try:
                candle = Candle.from_dict(item)
                candles.append(candle)
            except ValidationError as err:
                logger.warning(f"تجاهل شمعة غير صالحة: {err}")

        logger.info(f"تم بنجاح استخراج {len(candles)} شمعة لزوج {pair}.")
        return candles
