"""
tests/test_xai.py
اختبارات الوحدة المؤتمتة لطبقة تفسير قرارات نماذج الذكاء الاصطناعي (XAI - Sprint 8).
"""

import math
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from core.candle import Candle
from ml.explainability import FEATURE_NAMES, PredictionExplainer
from ml.models.logistic import LogisticForecaster
from services.forecast_service import ForecastService
from storage.sqlite_storage import SQLiteStorage


class TestPredictionExplainer(unittest.TestCase):
    """اختبارات محرك تفكيك القرارات وحساب المساهمات الفنية."""

    def test_explain_mismatched_dimensions_raises_error(self):
        features = [0.01, 0.02]
        weights = [1.0, 2.0, 3.0]
        with self.assertRaises(ValueError):
            PredictionExplainer.explain(features, weights)

    def test_explain_correct_attribution_and_sorting(self):
        # 5 ميزات مطابقة لـ FEATURE_NAMES
        features = [0.02, -0.01, 0.005, 0.60, 0.002]
        # أوزان محاكاة:
        # 1. Price Return: 0.02 * 2.0 = +0.04 (Bullish)
        # 2. SMA Distance: -0.01 * 1.5 = -0.015 (Bearish)
        # 3. Candle Range: 0.005 * -1.0 = -0.005 (Bearish)
        # 4. RSI:          0.60 * 0.5 = +0.30 (Bullish)
        # 5. MACD:         0.002 * 10.0 = +0.02 (Bullish)
        weights = [2.0, 1.5, -1.0, 0.5, 10.0]

        result = PredictionExplainer.explain(features, weights)

        self.assertEqual(len(result.top_bullish_factors), 3)
        self.assertEqual(len(result.top_bearish_factors), 2)

        # التحقق من أن أعلى عامل صاعد هو RSI (مساهمة 0.30)
        top_bull = result.top_bullish_factors[0]
        self.assertEqual(top_bull.name, "RSI (Normalized)")
        self.assertAlmostEqual(top_bull.contribution, 0.30, places=4)

        # التحقق من أن أشد عامل هابط هو SMA Distance (-0.015)
        top_bear = result.top_bearish_factors[0]
        self.assertEqual(top_bear.name, "SMA Distance")
        self.assertAlmostEqual(top_bear.contribution, -0.015, places=4)

        # التحقق من الأهمية الشاملة (Global Importance)
        self.assertEqual(len(result.global_importance), 5)
        self.assertEqual(result.global_importance["MACD"], 10.0)


class TestXAIIntegration(unittest.TestCase):
    """اختبار تكامل طبقة XAI مع تدريب النموذج وخدمة التنبؤ."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")
        self.service = ForecastService(storage=self.storage)

    def tearDown(self):
        self.storage.disconnect()

    def test_forecast_with_explain_flag(self):
        now = datetime.now()
        candles = []
        for i in range(80):
            delta = math.sin(i * 0.4) * 0.0050
            price = 1.0800 + delta
            candles.append(
                Candle(
                    pair="EUR/USD",
                    interval="1day",
                    timestamp=now + timedelta(days=i),
                    open=Decimal(str(round(price - 0.0005, 5))),
                    high=Decimal(str(round(price + 0.0010, 5))),
                    low=Decimal(str(round(price - 0.0010, 5))),
                    close=Decimal(str(round(price, 5))),
                )
            )
        self.storage.save_candles_bulk(candles)

        # توليد تقرير مع تفعيل explain=True
        report = self.service.generate_forecast(
            pair="EUR/USD", interval="1day", limit=80, explain=True
        )

        self.assertIsNotNone(report.explanation)
        assert report.explanation is not None

        # التحقق من وجود القوى المؤثرة والأهمية العامة
        self.assertIsInstance(report.explanation.top_bullish_factors, list)
        self.assertIsInstance(report.explanation.top_bearish_factors, list)
        self.assertEqual(len(report.explanation.global_importance), len(FEATURE_NAMES))


if __name__ == "__main__":
    unittest.main()
