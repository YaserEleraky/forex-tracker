"""
services/forex_service.py
منسق عمليات الفوركس مع دعم حساب المؤشرات الفنية.
"""

from __future__ import annotations
import time
from decimal import Decimal
from typing import Any

from api.sources.twelvedata import TwelveDataSource
from core.candle import Candle
from core.intervals import Interval
from core.logger import logger
from core.pair import CurrencyPair
from indicators.moving_averages import SMA, EMA
from indicators.momentum import RSI, MACD
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


class ForexService:
    """خدمة إدارة أسواق الفوركس والتنسيق بين مصادر البيانات، التخزين، والتحليل الفني."""

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
        self,
        pair: str = "EUR/USD",
        interval: str = "1day",
        limit: int = 1,
    ) -> list[Candle]:
        """جلب وتخزين الشموع لزوج وإطار زمني محدد مع الحفظ الجماعي."""
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)

        logger.info(
            f"جلب وتخزين {limit} شمعة لزوج {validated_pair.symbol} ({validated_interval.value})..."
        )
        candles = self.source.fetch_candles(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            limit=limit,
        )

        self.storage.save_candles_bulk(candles)
        return candles

    def fetch_and_store_multiple(
        self,
        pairs: list[str],
        interval: str = "1day",
        limit: int = 1,
    ) -> dict[str, list[Candle]]:
        """جلب وتخزين عدة أزواج بالتسلسل مع إضافة تأخير زمني لمنع تجاوز Rate Limit."""
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

            if i < len(pairs) - 1 and self.rate_limit_delay > 0:
                time.sleep(self.rate_limit_delay)

        return results

    def get_watchlist(self, pairs: list[str]) -> list[dict[str, Any]]:
        """إنشاء نظرة عامة سريعة لأسعار قائمة المراقبة."""
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
        self,
        pair: str = "EUR/USD",
        interval: str = "1day",
        limit: int = 10,
    ) -> list[Candle]:
        """استرجاع السجل من قاعدة البيانات لزوج وإطار زمني معين."""
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)
        return self.storage.get_candles(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            limit=limit,
        )

    def analyze_pair(
        self,
        pair: str = "EUR/USD",
        interval: str = "1day",
        limit: int = 50,
        indicators: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        تحليل الشموع المخزنة لزوج معين وحساب المؤشرات المطلوبة.
        """
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)

        # 1. جلب الشموع المخزنة محلياً
        candles = self.storage.get_candles(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            limit=limit,
        )

        if not candles:
            return {"pair": validated_pair.symbol, "candles_count": 0, "results": {}}

        # فرز تصاعدي زمني للحسابات الدقيقة
        candles_sorted = sorted(candles, key=lambda c: c.timestamp)
        requested_indicators = [
            ind.strip().lower() for ind in (indicators or ["sma", "rsi", "macd"])
        ]

        indicator_outputs: dict[str, Any] = {}

        # 2. حساب المؤشرات المطلوبة
        if "sma" in requested_indicators:
            indicator_outputs["sma_20"] = SMA(period=20).calculate(candles_sorted)

        if "ema" in requested_indicators:
            indicator_outputs["ema_20"] = EMA(period=20).calculate(candles_sorted)

        if "rsi" in requested_indicators:
            indicator_outputs["rsi_14"] = RSI(period=14).calculate(candles_sorted)

        if "macd" in requested_indicators:
            indicator_outputs["macd"] = MACD(
                fast_period=12, slow_period=26, signal_period=9
            ).calculate(candles_sorted)

        return {
            "pair": validated_pair.symbol,
            "interval": validated_interval.value,
            "candles_count": len(candles_sorted),
            "latest_candle": candles_sorted[-1],
            "indicators": indicator_outputs,
        }
