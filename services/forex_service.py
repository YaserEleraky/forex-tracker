from __future__ import annotations
from decimal import Decimal
from api.sources.twelvedata import TwelveDataSource
from core.candle import Candle
from core.logger import logger
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


class ForexService:
    """
    خدمة إدارة بيانات الفوركس وتنسيق العمليات بين مزودي البيانات والتخزين.
    """

    def __init__(
        self, source: TwelveDataSource | None = None, storage: Storage | None = None
    ) -> None:
        self.source = source or TwelveDataSource()
        self.storage = storage or SQLiteStorage()

    def get_current_price(self, pair: str = "EUR/USD") -> Decimal:
        """
        جلب السعر الحالي الفوري المباشر لزوج العملات (أحدث سعر إغلاق).
        """
        logger.info(f"طلب السعر اللحظي لزوج {pair} عبر ForexService...")
        candles = self.source.fetch_candles(pair=pair, limit=1)
        if not candles:
            raise ValueError(f"تعذر جلب السعر اللحظي لزوج {pair}")
        return candles[0].close

    def fetch_and_store(self, pair: str = "EUR/USD", limit: int = 1) -> list[Candle]:
        """
        جلب شمعة أو عدة شموع من الـ API وحفظها فوراً في التخزين الدائم.
        """
        logger.info(f"بدء عملية جلب وتخزين {limit} شمعة لزوج {pair}...")
        candles = self.source.fetch_candles(pair=pair, limit=limit)

        for candle in candles:
            self.storage.save_candle(candle)

        logger.info(f"تم بنجاح جلب وتخزين {len(candles)} شمعة لزوج {pair}.")
        return candles

    def get_history(self, pair: str = "EUR/USD", limit: int = 10) -> list[Candle]:
        """
        استرجاع الشموع المخزنة محلياً لزوج معين.
        """
        logger.info(f"قراءة آخر {limit} شمعة لزوج {pair} من قاعدة البيانات...")
        return self.storage.get_candles(pair=pair, limit=limit)
