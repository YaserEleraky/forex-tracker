from __future__ import annotations
from decimal import Decimal

from core.candle import Candle
from core.exceptions import ValidationError
from core.strategy import BaseStrategy
from core.trade import SignalType
from indicators.moving_averages import SMA


class SMACrossoverStrategy(BaseStrategy):
    """
    استراتيجية توليد إشارات الشراء والبيع عبر تقاطع متوسطين حسابيين (Fast vs Slow).
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30) -> None:
        if fast_period >= slow_period:
            raise ValidationError(
                f"فترة المتوسط السريع ({fast_period}) يجب أن تكون أصغر من فترة المتوسط البطيء ({slow_period})"
            )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self._fast_sma = SMA(period=fast_period)
        self._slow_sma = SMA(period=slow_period)

    @property
    def name(self) -> str:
        return f"SMA_Crossover({self.fast_period}/{self.slow_period})"

    def generate_signal(self, index: int, candles: list[Candle]) -> SignalType:
        """
        تقييم الشمعة الحالية ومقارنتها بالشمعة السابقة لتحديد حدوث تقاطع.
        """
        # نحتاج على الأقل عدد شموع كافي لحساب المتوسط البطيء + شمعة للمقارنة السابقة
        if index < self.slow_period:
            return SignalType.HOLD

        # نقتطع الشموع حتى اللحظة الحالية فقط لمنع Lookahead Bias
        sub_candles = candles[: index + 1]

        # حساب المتوسطات
        fast_series = self._fast_sma.calculate(sub_candles)
        slow_series = self._slow_sma.calculate(sub_candles)

        # استخراج قيم الشمعة الحالية والشمعة السابقة
        curr_fast = fast_series[-1].value
        curr_slow = slow_series[-1].value
        prev_fast = fast_series[-2].value
        prev_slow = slow_series[-2].value

        if None in (curr_fast, curr_slow, prev_fast, prev_slow):
            return SignalType.HOLD

        assert curr_fast is not None and curr_slow is not None
        assert prev_fast is not None and prev_slow is not None

        # 1. تقاطع صاعد (Golden Cross): السريع كان تحت أو يساوي البطيء وأصبح فوقه
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return SignalType.BUY

        # 2. تقاطع هابط (Death Cross): السريع كان فوق أو يساوي البطيء وأصبح تحته
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return SignalType.SELL

        return SignalType.HOLD
