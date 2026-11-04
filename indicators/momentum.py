"""
indicators/momentum.py
حساب مؤشرات الزخم والاتجاه: RSI و MACD بدقة Decimal مع معالجة النوع الصارم (Type Guarding).
"""

from __future__ import annotations
from decimal import Decimal
from core.candle import Candle
from core.exceptions import ValidationError
from indicators.base import BaseIndicator, IndicatorResult


class RSI(BaseIndicator):
    """Relative Strength Index (مؤشر القوة النسبية بطريقة Wilder's Smoothing)."""

    def __init__(self, period: int = 14) -> None:
        if period < 1:
            raise ValidationError("يجب أن تكون فترة RSI أكبر من أو تساوي 1")
        self.period = period
        self.name = f"RSI_{self.period}"

    def calculate(self, candles: list[Candle]) -> list[IndicatorResult]:
        results: list[IndicatorResult] = []
        if not candles:
            return results

        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        n = len(sorted_candles)

        if n <= self.period:
            return [
                IndicatorResult(name=self.name, timestamp=c.timestamp, value=None)
                for c in sorted_candles
            ]

        # 1. حساب الفروقات اليومية (Gains & Losses)
        gains: list[Decimal] = [Decimal("0")]
        losses: list[Decimal] = [Decimal("0")]

        for i in range(1, n):
            delta = sorted_candles[i].close - sorted_candles[i - 1].close
            if delta > Decimal("0"):
                gains.append(delta)
                losses.append(Decimal("0"))
            else:
                gains.append(Decimal("0"))
                losses.append(abs(delta))

        # أول (period) شمعة تكون نتيجتها None
        for i in range(self.period):
            results.append(
                IndicatorResult(
                    name=self.name, timestamp=sorted_candles[i].timestamp, value=None
                )
            )

        # 2. حساب المتوسط الأولي (SMA للربح والخسارة)
        first_avg_gain = sum(gains[1 : self.period + 1], Decimal("0")) / Decimal(
            str(self.period)
        )
        first_avg_loss = sum(losses[1 : self.period + 1], Decimal("0")) / Decimal(
            str(self.period)
        )

        avg_gain = first_avg_gain
        avg_loss = first_avg_loss

        # حساب أول نقطة RSI
        rsi_val = self._compute_rsi(avg_gain, avg_loss)
        results.append(
            IndicatorResult(
                name=self.name,
                timestamp=sorted_candles[self.period].timestamp,
                value=rsi_val,
            )
        )

        # 3. تمهيد ويلدر (Wilder's Smoothing) للشموع المتبقية
        period_dec = Decimal(str(self.period))
        for i in range(self.period + 1, n):
            avg_gain = (
                (avg_gain * (period_dec - Decimal("1"))) + gains[i]
            ) / period_dec
            avg_loss = (
                (avg_loss * (period_dec - Decimal("1"))) + losses[i]
            ) / period_dec

            rsi_val = self._compute_rsi(avg_gain, avg_loss)
            results.append(
                IndicatorResult(
                    name=self.name, timestamp=sorted_candles[i].timestamp, value=rsi_val
                )
            )

        return results

    def _compute_rsi(self, avg_gain: Decimal, avg_loss: Decimal) -> Decimal:
        if avg_loss == Decimal("0"):
            return Decimal("100.00")
        if avg_gain == Decimal("0"):
            return Decimal("0.00")

        rs = avg_gain / avg_loss
        rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
        return round(rsi, 2)


class MACD(BaseIndicator):
    """
    Moving Average Convergence Divergence (MACD).
    يستخرج: MACD Line، Signal Line، و Histogram.
    """

    def __init__(
        self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
    ) -> None:
        if not (fast_period < slow_period and signal_period >= 1):
            raise ValidationError(
                "شروط فترات MACD: fast_period < slow_period و signal_period >= 1"
            )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = f"MACD_{self.fast_period}_{self.slow_period}_{self.signal_period}"

    def calculate(self, candles: list[Candle]) -> list[IndicatorResult]:
        results: list[IndicatorResult] = []
        if not candles:
            return results

        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        closes = [c.close for c in sorted_candles]
        n = len(closes)

        # 1. حساب Fast EMA و Slow EMA
        fast_ema = self._calculate_ema_series(closes, self.fast_period)
        slow_ema = self._calculate_ema_series(closes, self.slow_period)

        # 2. خط الماكد = Fast EMA - Slow EMA
        macd_line: list[Decimal | None] = []
        for f, s in zip(fast_ema, slow_ema):
            if f is not None and s is not None:
                macd_line.append(f - s)
            else:
                macd_line.append(None)

        # 3. خط الإشارة = EMA(9) لخط الماكد
        signal_line = self._calculate_ema_series_from_nullable(
            macd_line, self.signal_period
        )

        # 4. تجميع النتائج مع الهيستوجرام
        for i in range(n):
            m_val = macd_line[i]
            s_val = signal_line[i]

            m_rounded = round(m_val, 5) if m_val is not None else None
            s_rounded = round(s_val, 5) if s_val is not None else None
            hist_val = (
                (m_rounded - s_rounded)
                if (m_rounded is not None and s_rounded is not None)
                else None
            )

            extra = {
                "macd": m_rounded,
                "signal": s_rounded,
                "histogram": hist_val,
            }

            results.append(
                IndicatorResult(
                    name=self.name,
                    timestamp=sorted_candles[i].timestamp,
                    value=extra["macd"],
                    extra=extra,
                )
            )

        return results

    def _calculate_ema_series(
        self, series: list[Decimal], period: int
    ) -> list[Decimal | None]:
        results: list[Decimal | None] = []
        multiplier = Decimal("2") / Decimal(str(period + 1))
        prev_ema: Decimal | None = None

        for i, val in enumerate(series):
            if i + 1 < period:
                results.append(None)
            elif i + 1 == period:
                sma = sum(series[:period], Decimal("0")) / Decimal(str(period))
                prev_ema = sma
                results.append(sma)
            else:
                assert prev_ema is not None, "prev_ema must be calculated"
                current_ema = (val * multiplier) + (
                    prev_ema * (Decimal("1") - multiplier)
                )
                prev_ema = current_ema
                results.append(current_ema)
        return results

    def _calculate_ema_series_from_nullable(
        self, series: list[Decimal | None], period: int
    ) -> list[Decimal | None]:
        results: list[Decimal | None] = [None] * len(series)
        valid_indices = [idx for idx, v in enumerate(series) if v is not None]

        if len(valid_indices) < period:
            return results

        multiplier = Decimal("2") / Decimal(str(period + 1))
        start_idx = valid_indices[period - 1]

        # SMA الأولي لخط الإشارة
        initial_slice = [
            series[i] for i in valid_indices[:period] if series[i] is not None
        ]
        prev_ema: Decimal | None = sum(
            (v for v in initial_slice if v is not None), Decimal("0")
        ) / Decimal(str(period))
        results[start_idx] = prev_ema

        # استكمال حساب الـ EMA لباقي القيم
        for idx in valid_indices[period:]:
            val = series[idx]
            if val is not None and prev_ema is not None:
                current_ema = (val * multiplier) + (
                    prev_ema * (Decimal("1") - multiplier)
                )
                prev_ema = current_ema
                results[idx] = current_ema

        return results
