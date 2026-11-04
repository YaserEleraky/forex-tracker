import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from core.candle import Candle
from core.exceptions import ValidationError
from indicators.moving_averages import SMA, EMA
from indicators.momentum import RSI, MACD


class TestMovingAverages(unittest.TestCase):
    """اختبارات دقة حساب المتوسطات المتحركة."""

    def setUp(self):
        self.now = datetime(2026, 11, 1, 10, 0)
        # 5 شموع متتالية بأسعار إغلاق: 10, 11, 12, 13, 14
        self.candles = [
            Candle(
                pair="EUR/USD",
                timestamp=self.now + timedelta(days=i),
                open=Decimal("10"),
                high=Decimal("15"),
                low=Decimal("9"),
                close=Decimal(str(10 + i)),
            )
            for i in range(5)
        ]

    def test_sma_calculation(self):
        sma = SMA(period=3)
        results = sma.calculate(self.candles)

        self.assertEqual(len(results), 5)
        # أول شمعتين يجب أن تكونا None لأن الفترة 3
        self.assertIsNone(results[0].value)
        self.assertIsNone(results[1].value)

        # الشمعة الثالثة: (10 + 11 + 12) / 3 = 11.0
        self.assertEqual(results[2].value, Decimal("11.00000"))
        # الشمعة الرابعة: (11 + 12 + 13) / 3 = 12.0
        self.assertEqual(results[3].value, Decimal("12.00000"))
        # الشمعة الخامسة: (12 + 13 + 14) / 3 = 13.0
        self.assertEqual(results[4].value, Decimal("13.00000"))

    def test_ema_calculation(self):
        ema = EMA(period=3)
        results = ema.calculate(self.candles)

        self.assertEqual(len(results), 5)
        self.assertIsNone(results[0].value)
        self.assertIsNone(results[1].value)

        # أول نقطة EMA هي نفس قيمة SMA لنفس الفترة = 11.0
        self.assertEqual(results[2].value, Decimal("11.00000"))

        # الشمعة التالية: Multiplier = 2 / (3 + 1) = 0.5
        # EMA = (13 * 0.5) + (11.0 * 0.5) = 6.5 + 5.5 = 12.0
        self.assertEqual(results[3].value, Decimal("12.00000"))

    def test_invalid_period_raises(self):
        with self.assertRaises(ValidationError):
            SMA(period=0)
        with self.assertRaises(ValidationError):
            EMA(period=-5)


class TestMomentumIndicators(unittest.TestCase):
    """اختبارات مؤشرات الزخم والاتجاه: RSI و MACD."""

    def test_rsi_constant_gains(self):
        # في حالة صعود مستمر بدون أي خسارة، يجب أن يكون RSI = 100
        now = datetime.now()
        candles = [
            Candle(
                pair="EUR/USD",
                timestamp=now + timedelta(days=i),
                open=Decimal("1.0"),
                high=Decimal("1.2"),
                low=Decimal("0.9"),
                close=Decimal(str(1.0 + (i * 0.1))),
            )
            for i in range(16)
        ]

        rsi = RSI(period=14)
        results = rsi.calculate(candles)

        self.assertEqual(len(results), 16)
        # بعد اكتمال فترة الـ 14، يجب أن يكون المؤشر 100 لعدم وجود خسائر
        self.assertEqual(results[-1].value, Decimal("100.00"))

    def test_macd_structure_and_types(self):
        now = datetime.now()
        candles = [
            Candle(
                pair="EUR/USD",
                timestamp=now + timedelta(days=i),
                open=Decimal("1.0"),
                high=Decimal("1.2"),
                low=Decimal("0.9"),
                close=Decimal(str(1.05 + (i * 0.005 if i % 2 == 0 else -0.002))),
            )
            for i in range(35)
        ]

        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        results = macd.calculate(candles)

        self.assertEqual(len(results), 35)
        latest_res = results[-1].extra

        # Type narrowing صريح لإسكات Pylance
        self.assertIsNotNone(latest_res)
        assert latest_res is not None

        self.assertIn("macd", latest_res)
        self.assertIn("signal", latest_res)
        self.assertIn("histogram", latest_res)

        # التأكد من صحة علاقة الهيستوجرام: Histogram = MACD - Signal
        if latest_res["macd"] is not None and latest_res["signal"] is not None:
            expected_hist = latest_res["macd"] - latest_res["signal"]
            self.assertEqual(latest_res["histogram"], expected_hist)

    def test_macd_invalid_periods(self):
        with self.assertRaises(ValidationError):
            # fast_period يجب أن يكون أصغر من slow_period
            MACD(fast_period=30, slow_period=20, signal_period=9)


if __name__ == "__main__":
    unittest.main()
