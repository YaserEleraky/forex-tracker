from __future__ import annotations
import math
from typing import Any
from core.candle import Candle
from indicators.moving_averages import SMA
from indicators.momentum import RSI, MACD


class FeatureExtractor:
    """استخراج مصفوفات الميزات الرقمية والهدف التصنيفي للشمعة القادمة."""

    def __init__(self, rsi_period: int = 14, sma_period: int = 20) -> None:
        self.rsi_period = rsi_period
        self.sma_period = sma_period
        self._rsi = RSI(period=rsi_period)
        self._sma = SMA(period=sma_period)
        self._macd = MACD(fast_period=12, slow_period=26, signal_period=9)

    def extract_features(
        self, candles: list[Candle]
    ) -> tuple[list[list[float]], list[int]]:
        """
        تحويل سلسلة الشموع إلى مصفوفة ميزات (X) ومصفوفة أهداف تصنيفية (y).

        y = 1: الشمعة القادمة صاعدة (Close_{t+1} > Close_t)
        y = 0: الشمعة القادمة هابطة أو متساوية (Close_{t+1} <= Close_t)
        """
        # نحتاج على الأقل عدد شموع كافٍ لحساب MACD البطيء (26) + شمعة الهدف القادمة (+1)
        min_required = 35
        if len(candles) < min_required:
            return [], []

        candles_sorted = sorted(candles, key=lambda c: c.timestamp)

        # حساب سلاسل المؤشرات الفنية
        rsi_series = self._rsi.calculate(candles_sorted)
        sma_series = self._sma.calculate(candles_sorted)
        macd_series = self._macd.calculate(candles_sorted)

        X: list[list[float]] = []
        y: list[int] = []

        # نبدأ من الفهرس الذي تتوفر فيه جميع المؤشرات وحتى الشمعة قبل الأخيرة (لتوفير target للشمعة التالية)
        start_idx = 30
        for i in range(start_idx, len(candles_sorted) - 1):
            curr_c = candles_sorted[i]
            prev_c = candles_sorted[i - 1]
            next_c = candles_sorted[i + 1]

            rsi_val = rsi_series[i].value
            sma_val = sma_series[i].value
            macd_val = macd_series[i].value

            if None in (rsi_val, sma_val, macd_val):
                continue

            assert rsi_val is not None and sma_val is not None and macd_val is not None

            # 1. نسبة التغير في السعر للشمعة الحالية
            price_return = float((curr_c.close - prev_c.close) / prev_c.close)

            # 2. انحراف السعر الحالي عن المتوسط المتحرك البسيط (SMA Distance %)
            sma_diff = float((curr_c.close - sma_val) / sma_val)

            # 3. المدى السعري النسبي للشمعة (High - Low) / Close
            candle_range = float((curr_c.high - curr_c.low) / curr_c.close)

            # 4. قيم المؤشرات
            rsi_norm = float(rsi_val) / 100.0  # تطبيع RSI بين 0 و 1
            macd_norm = float(macd_val)

            feature_vector = [
                price_return,
                sma_diff,
                candle_range,
                rsi_norm,
                macd_norm,
            ]
            X.append(feature_vector)

            # تحديد الهدف: هل أغلقت الشمعة التالية أعلى من الحالية؟
            target = 1 if next_c.close > curr_c.close else 0
            y.append(target)

        return X, y

    def extract_latest_features(self, candles: list[Candle]) -> list[float] | None:
        """
        استخراج متجه الميزات للشمعة الأخيرة فقط لتوليد التنبؤ الحي.
        """
        if len(candles) < 35:
            return None

        candles_sorted = sorted(candles, key=lambda c: c.timestamp)
        rsi_series = self._rsi.calculate(candles_sorted)
        sma_series = self._sma.calculate(candles_sorted)
        macd_series = self._macd.calculate(candles_sorted)

        curr_c = candles_sorted[-1]
        prev_c = candles_sorted[-2]

        rsi_val = rsi_series[-1].value
        sma_val = sma_series[-1].value
        macd_val = macd_series[-1].value

        if None in (rsi_val, sma_val, macd_val):
            return None

        assert rsi_val is not None and sma_val is not None and macd_val is not None

        return [
            float((curr_c.close - prev_c.close) / prev_c.close),
            float((curr_c.close - sma_val) / sma_val),
            float((curr_c.high - curr_c.low) / curr_c.close),
            float(rsi_val) / 100.0,
            float(macd_val),
        ]
