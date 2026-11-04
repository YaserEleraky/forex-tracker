from __future__ import annotations
from decimal import Decimal
from core.candle import Candle
from core.exceptions import ValidationError
from indicators.base import BaseIndicator, IndicatorResult


class SMA(BaseIndicator):
    """Simple Moving Average (المتوسط المتحرك البسيط)."""

    def __init__(self, period: int = 20) -> None:
        if period < 1:
            raise ValidationError("يجب أن تكون فترة حساب SMA أكبر من أو تساوي 1")
        self.period = period
        self.name = f"SMA_{self.period}"

    def calculate(self, candles: list[Candle]) -> list[IndicatorResult]:
        results: list[IndicatorResult] = []
        if not candles:
            return results

        sorted_candles = sorted(candles, key=lambda c: c.timestamp)

        for i, candle in enumerate(sorted_candles):
            if i + 1 < self.period:
                results.append(
                    IndicatorResult(
                        name=self.name, timestamp=candle.timestamp, value=None
                    )
                )
            else:
                window = sorted_candles[i + 1 - self.period : i + 1]
                avg = sum((c.close for c in window), Decimal("0")) / Decimal(
                    str(self.period)
                )
                results.append(
                    IndicatorResult(
                        name=self.name, timestamp=candle.timestamp, value=round(avg, 5)
                    )
                )

        return results


class EMA(BaseIndicator):
    """Exponential Moving Average (المتوسط المتحرك الأسي)."""

    def __init__(self, period: int = 20) -> None:
        if period < 1:
            raise ValidationError("يجب أن تكون فترة حساب EMA أكبر من أو تساوي 1")
        self.period = period
        self.name = f"EMA_{self.period}"
        self.multiplier = Decimal("2") / Decimal(str(self.period + 1))

    def calculate(self, candles: list[Candle]) -> list[IndicatorResult]:
        results: list[IndicatorResult] = []
        if not candles:
            return results

        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        prev_ema: Decimal | None = None

        for i, candle in enumerate(sorted_candles):
            if i + 1 < self.period:
                results.append(
                    IndicatorResult(
                        name=self.name, timestamp=candle.timestamp, value=None
                    )
                )
            elif i + 1 == self.period:
                window = sorted_candles[: self.period]
                sma = sum((c.close for c in window), Decimal("0")) / Decimal(
                    str(self.period)
                )
                prev_ema = sma
                results.append(
                    IndicatorResult(
                        name=self.name, timestamp=candle.timestamp, value=round(sma, 5)
                    )
                )
            else:
                current_ema = (candle.close * self.multiplier) + (
                    (prev_ema or Decimal("0")) * (Decimal("1") - self.multiplier)
                )
                prev_ema = current_ema
                results.append(
                    IndicatorResult(
                        name=self.name,
                        timestamp=candle.timestamp,
                        value=round(current_ema, 5),
                    )
                )

        return results
