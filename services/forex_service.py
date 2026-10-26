from __future__ import annotations
import time
from decimal import Decimal
from typing import Any
from api.sources.twelvedata import TwelveDataSource
from core.candle import Candle
from core.intervals import Interval
from core.logger import logger
from core.pair import CurrencyPair
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


class ForexService:
    """خدمة إدارة أسواق الفوركس والتنسيق بين مصادر البيانات والتخزين."""

    def __init__(
        self,
        source: TwelveDataSource | None = None,
        storage: Storage | None = None,
        rate_limit_delay: float = 1.0,
    ) -> None:
        self.source = source or TwelveDataSource()
        self.storage = storage or SQLiteStorage()
        self.rate_limit_delay = rate_limit_delay

    def get_current_price(self, pair: str = "EUR/USD") -> Decimal:
        """جلب السعر الحالي اللحظي لزوج عملات بعد التحقق من صحته."""
        validated_pair = CurrencyPair.from_string(pair)
        logger.info(f"طلب السعر اللحظي لزوج {validated_pair.symbol}...")
        candles = self.source.fetch_candles(pair=validated_pair.symbol, limit=1)
        if not candles:
            raise ValueError(f"تعذر جلب السعر لزوج {validated_pair.symbol}")
        return candles[0].close

    def fetch_and_store(
        self, pair: str = "EUR/USD", interval: str = "1day", limit: int = 1
    ) -> list[Candle]:
        """
        جلب وتخزين الشموع لزوج وإطار زمني محدد مع الحفظ الجماعي.
        """
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)

        logger.info(
            f"جلب وتخزين {limit} شمعة لزوج {validated_pair.symbol} ({validated_interval.value})..."
        )
        candles = self.source.fetch_candles(
            pair=validated_pair.symbol, interval=validated_interval.value, limit=limit
        )

        # الحفظ الجماعي السريع
        self.storage.save_candles_bulk(candles)
        return candles

    def fetch_and_store_multiple(
        self, pairs: list[str], interval: str = "1day", limit: int = 1
    ) -> dict[str, list[Candle]]:
        """
        جلب وتخزين عدة أزواج بالتسلسل مع إضافة تأخير زمني لمنع تجاوز Rate Limit.
        """
        results: dict[str, list[Candle]] = {}

        for i, pair_str in enumerate(pairs):
            try:
                candles = self.fetch_and_store(
                    pair=pair_str, interval=interval, limit=limit
                )
                results[pair_str] = candles
            except Exception as err:
                logger.error(f"فشل جلب الزوج {pair_str}: {err}")
                results[pair_str] = []

            # تطبيق التأخير الزمني بين الطلبات باستثناء الطلب الأخير
            if i < len(pairs) - 1 and self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

        return results

    def get_watchlist(self, pairs: list[str]) -> list[dict[str, Any]]:
        """
        إنشاء نظرة عامة سريعة لأسعار قائمة المراقبة (Watchlist).
        """
        summary: list[dict[str, Any]] = []
        for i, pair_str in enumerate(pairs):
            try:
                pair_obj = CurrencyPair.from_string(pair_str)
                candles = self.source.fetch_candles(pair=pair_obj.symbol, limit=1)
                if candles:
                    c = candles[0]
                    summary.append(
                        {
                            "pair": pair_obj.symbol,
                            "close": c.close,
                            "high": c.high,
                            "low": c.low,
                            "time": c.timestamp,
                        }
                    )
            except Exception as err:
                logger.warning(f"تعذر قراءة بيانات المراقبة لـ {pair_str}: {err}")

            if i < len(pairs) - 1 and self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

        return summary

    def get_history(
        self, pair: str = "EUR/USD", interval: str = "1day", limit: int = 10
    ) -> list[Candle]:
        """استرجاع السجل من قاعدة البيانات لزوج وإطار زمني معين."""
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)
        return self.storage.get_candles(
            pair=validated_pair.symbol, interval=validated_interval.value, limit=limit
        )
