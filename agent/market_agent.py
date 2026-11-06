"""
agent/market_agent.py
وكيل ذكي مدمج لتحليل الأسواق ودمج مخرجات المؤشرات، النماذج، والـ XAI.
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from core.candle import Candle
from core.exceptions import ValidationError
from core.logger import logger
from services.forecast_service import ForecastReport, ForecastService
from services.forex_service import ForexService


@dataclass
class AgentAssessment:
    """التقرير النهائي الصادر من الوكيل الذكي."""

    pair: str
    interval: str
    current_price: Decimal
    recommended_action: str  # "BUY", "SELL", "WAIT"
    confidence_score: float  # نسبة مئوية 0 - 100%
    market_regime: str  # "Trending Up", "Trending Down", "Ranging / Neutral"
    technical_bias: str  # انحياز المؤشرات الفنية
    ml_bias: str  # انحياز نموذج التعلّم الآلي
    key_reasons: list[str]  # الأسباب الجوهرية للقرار
    narrative: str  # ملخص سردي للمتداول

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "interval": self.interval,
            "current_price": float(self.current_price),
            "recommended_action": self.recommended_action,
            "confidence_score": round(self.confidence_score, 1),
            "market_regime": self.market_regime,
            "technical_bias": self.technical_bias,
            "ml_bias": self.ml_bias,
            "key_reasons": self.key_reasons,
            "narrative": self.narrative,
        }


class ForexAgent:
    """وكيل ذكي يجمع التحليل الفني والتعلم الآلي لتقييم فرص السوق."""

    def __init__(
        self,
        forex_service: ForexService | None = None,
        forecast_service: ForecastService | None = None,
    ) -> None:
        self.forex_service = forex_service or ForexService()
        self.forecast_service = forecast_service or ForecastService()

    def analyze_market(
        self,
        pair: str = "EUR/USD",
        interval: str = "1day",
        limit: int = 120,
    ) -> AgentAssessment:
        """
        إجراء تحليل شامل يدمج السعر اللحظي، المؤشرات، التنبؤ، وتفسير XAI.
        """
        # 1. جلب السعر والتحليل الفني
        current_price = self.forex_service.get_current_price(pair=pair)
        tech_data = self.forex_service.analyze_pair(
            pair=pair,
            interval=interval,
            limit=limit,
            indicators=["sma", "rsi", "macd"],
        )

        # 2. جلب تنبؤ الـ ML وتفسير الـ XAI
        forecast = self.forecast_service.generate_forecast(
            pair=pair,
            interval=interval,
            limit=limit,
            explain=True,
        )

        # 3. وزن الإشارات وحساب توافق التحليل
        return self._synthesize_analysis(
            pair, interval, current_price, tech_data, forecast
        )

    def _synthesize_analysis(
        self,
        pair: str,
        interval: str,
        current_price: Decimal,
        tech_data: dict[str, Any],
        forecast: ForecastReport,
    ) -> AgentAssessment:
        """دمج الإشارات المتعددة وتحديد التوصية وثقة الوكيل."""
        reasons: list[str] = []
        bullish_points = 0
        bearish_points = 0

        # أ) تقييم المؤشرات الفنية (Technical Analysis)
        indicators = tech_data.get("indicators", {})

        # 1. فحص SMA
        sma_series = indicators.get("sma_20", [])
        if sma_series and sma_series[-1].value is not None:
            sma_val = Decimal(str(sma_series[-1].value))
            if current_price > sma_val:
                bullish_points += 1
                reasons.append(
                    f"Price ({current_price:.5f}) is trading above 20-period SMA ({sma_val:.5f})."
                )
            else:
                bearish_points += 1
                reasons.append(
                    f"Price ({current_price:.5f}) is trading below 20-period SMA ({sma_val:.5f})."
                )

        # 2. فحص RSI
        rsi_series = indicators.get("rsi_14", [])
        if rsi_series and rsi_series[-1].value is not None:
            rsi_val = float(rsi_series[-1].value)
            if rsi_val > 70:
                bearish_points += 1
                reasons.append(f"RSI is overbought at {rsi_val:.1f} (reversal risk).")
            elif rsi_val < 30:
                bullish_points += 1
                reasons.append(f"RSI is oversold at {rsi_val:.1f} (potential bounce).")
            elif rsi_val >= 50:
                bullish_points += 1
                reasons.append(f"RSI shows positive momentum at {rsi_val:.1f}.")
            else:
                bearish_points += 1
                reasons.append(f"RSI shows weak momentum at {rsi_val:.1f}.")

        # 3. فحص MACD
        macd_series = indicators.get("macd", [])
        if macd_series and macd_series[-1].extra and macd_series[-1].extra.get("histogram") is not None:
            hist = float(macd_series[-1].extra["histogram"])
            if hist > 0:
                bullish_points += 1
                reasons.append(f"MACD Histogram is positive (+{hist:.5f}).")
            else:
                bearish_points += 1
                reasons.append(f"MACD Histogram is negative ({hist:.5f}).")

        tech_bias = (
            "BULLISH"
            if bullish_points > bearish_points
            else ("BEARISH" if bearish_points > bullish_points else "NEUTRAL")
        )

        # ب) تقييم تنبؤ التعلّم الآلي (Machine Learning + XAI)
        ml_bias = forecast.direction
        if forecast.direction == "UP" and forecast.up_probability >= 55.0:
            bullish_points += 2
            reasons.append(
                f"ML Model predicts UP direction with {forecast.up_probability:.1f}% probability."
            )
        elif forecast.direction == "DOWN" and forecast.down_probability >= 55.0:
            bearish_points += 2
            reasons.append(
                f"ML Model predicts DOWN direction with {forecast.down_probability:.1f}% probability."
            )
        else:
            reasons.append(
                f"ML Model probability is neutral ({forecast.up_probability:.1f}% UP)."
            )

        # دمج أسباب XAI الرئيسية
        if forecast.explanation:
            if forecast.direction == "UP" and forecast.explanation.top_bullish_factors:
                top_driver = forecast.explanation.top_bullish_factors[0]
                reasons.append(
                    f"Top XAI Driver: {top_driver.name} is supporting upward movement."
                )
            elif (
                forecast.direction == "DOWN"
                and forecast.explanation.top_bearish_factors
            ):
                top_drag = forecast.explanation.top_bearish_factors[0]
                reasons.append(
                    f"Top XAI Drag: {top_drag.name} is adding downward pressure."
                )

        # ج) اتخاذ القرار وحساب نسبة الثقة
        total_points = bullish_points + bearish_points
        net_bias = bullish_points - bearish_points

        if net_bias >= 2 and bullish_points >= 3:
            action = "BUY"
            market_regime = "Bullish Expansion"
            confidence = min(85.0, 50.0 + (bullish_points / total_points) * 40.0)
        elif net_bias <= -2 and bearish_points >= 3:
            action = "SELL"
            market_regime = "Bearish Correction"
            confidence = min(85.0, 50.0 + (bearish_points / total_points) * 40.0)
        else:
            action = "WAIT"
            market_regime = "Consolidation / Mixed Signals"
            confidence = 50.0

        # د) صياغة الملخص السردي
        narrative = (
            f"Market for {pair} is currently in a {market_regime}. "
            f"Technical indicators lean {tech_bias.lower()}, while the predictive ML model signals {ml_bias}. "
            f"Given the confluence of signals, the recommended tactical posture is to {action} with {confidence:.0f}% confidence."
        )

        return AgentAssessment(
            pair=pair,
            interval=interval,
            current_price=current_price,
            recommended_action=action,
            confidence_score=confidence,
            market_regime=market_regime,
            technical_bias=tech_bias,
            ml_bias=ml_bias,
            key_reasons=reasons,
            narrative=narrative,
        )
