"""
tests/test_agent.py
اختبارات الوحدة المؤتمتة للوكيل الذكي Forex AI Agent (Sprint 9).
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from agent.market_agent import AgentAssessment, ForexAgent
from ml.explainability import ExplanationResult, FeatureImpact
from services.forecast_service import ForecastReport


class TestForexAgent(unittest.TestCase):
    """اختبارات محرك اتخاذ القرار ودمج إشارات التحليل الفني والتعلم الآلي."""

    def setUp(self):
        self.mock_forex_service = MagicMock()
        self.mock_forecast_service = MagicMock()
        self.agent = ForexAgent(
            forex_service=self.mock_forex_service,
            forecast_service=self.mock_forecast_service,
        )

    def test_synthesize_bullish_confluence_leads_to_buy(self):
        # 1. إعداد بيانات فنية صاعدة بالكامل
        current_price = Decimal("1.1200")

        mock_sma_point = MagicMock()
        mock_sma_point.value = Decimal("1.1100")  # السعر أعلى من المتوسط

        mock_rsi_point = MagicMock()
        mock_rsi_point.value = 58.0  # زخم إيجابي دون تشبع

        mock_macd_point = MagicMock()
        mock_macd_point.histogram = Decimal("0.0015")  # هيستوجرام موجب

        tech_data = {
            "indicators": {
                "sma_20": [mock_sma_point],
                "rsi_14": [mock_rsi_point],
                "macd": [mock_macd_point],
            }
        }

        # 2. إعداد تقرير تنبؤ ذكاء اصطناعي صاعد
        mock_forecast = ForecastReport(
            pair="EUR/USD",
            interval="1day",
            model_name="LogisticRegression",
            last_candle_time="2026-11-06 00:00",
            latest_close=current_price,
            direction="UP",
            up_probability=65.0,
            down_probability=35.0,
            test_accuracy=60.0,
            train_samples=80,
            test_samples=20,
            explanation=ExplanationResult(
                top_bullish_factors=[
                    FeatureImpact(
                        name="RSI (Normalized)",
                        feature_value=0.58,
                        weight=1.2,
                        contribution=0.696,
                        impact_type="BULLISH",
                    )
                ],
                top_bearish_factors=[],
                global_importance={"RSI (Normalized)": 1.2},
            ),
        )

        assessment = self.agent._synthesize_analysis(
            pair="EUR/USD",
            interval="1day",
            current_price=current_price,
            tech_data=tech_data,
            forecast=mock_forecast,
        )

        self.assertEqual(assessment.recommended_action, "BUY")
        self.assertEqual(assessment.technical_bias, "BULLISH")
        self.assertEqual(assessment.ml_bias, "UP")
        self.assertGreater(assessment.confidence_score, 50.0)
        self.assertIn("Bullish Expansion", assessment.market_regime)
        self.assertTrue(len(assessment.key_reasons) >= 4)

    def test_synthesize_conflicting_signals_leads_to_wait(self):
        # حالة تضارب: المؤشرات الفنية هابطة ونموذج الـ ML صاعد باحتمالية ضعيفة
        current_price = Decimal("1.0900")

        mock_sma_point = MagicMock()
        mock_sma_point.value = Decimal("1.1100")  # السعر تحت المتوسط

        mock_rsi_point = MagicMock()
        mock_rsi_point.value = 45.0  # زخم سلبي ضعيف

        mock_macd_point = MagicMock()
        mock_macd_point.histogram = Decimal("-0.0010")  # هيستوجرام سالب

        tech_data = {
            "indicators": {
                "sma_20": [mock_sma_point],
                "rsi_14": [mock_rsi_point],
                "macd": [mock_macd_point],
            }
        }

        mock_forecast = ForecastReport(
            pair="EUR/USD",
            interval="1day",
            model_name="LogisticRegression",
            last_candle_time="2026-11-06 00:00",
            latest_close=current_price,
            direction="UP",
            up_probability=51.0,  # احتمالية صعود غير حاسمة
            down_probability=49.0,
            test_accuracy=55.0,
            train_samples=80,
            test_samples=20,
            explanation=None,
        )

        assessment = self.agent._synthesize_analysis(
            pair="EUR/USD",
            interval="1day",
            current_price=current_price,
            tech_data=tech_data,
            forecast=mock_forecast,
        )

        self.assertEqual(assessment.recommended_action, "WAIT")
        self.assertEqual(assessment.market_regime, "Consolidation / Mixed Signals")
        self.assertEqual(assessment.confidence_score, 50.0)


if __name__ == "__main__":
    unittest.main()
