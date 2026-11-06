from __future__ import annotations
from dataclasses import dataclass
from typing import Any

FEATURE_NAMES = [
    "Price Return",
    "SMA Distance",
    "Candle Range",
    "RSI (Normalized)",
    "MACD",
]


@dataclass
class FeatureImpact:
    """كائن يمثل تأثير ميزة محددة على القرار."""

    name: str
    feature_value: float
    weight: float
    contribution: float  # feature_value * weight
    impact_type: str  # "BULLISH" أو "BEARISH"


@dataclass
class ExplanationResult:
    """تقرير تفسير قرار التنبؤ."""

    top_bullish_factors: list[FeatureImpact]
    top_bearish_factors: list[FeatureImpact]
    global_importance: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_bullish_factors": [
                {"name": f.name, "contribution": round(f.contribution, 4)}
                for f in self.top_bullish_factors
            ],
            "top_bearish_factors": [
                {"name": f.name, "contribution": round(f.contribution, 4)}
                for f in self.top_bearish_factors
            ],
            "global_importance": {
                k: round(v, 4) for k, v in self.global_importance.items()
            },
        }


class PredictionExplainer:
    """تحليل مساهمة المؤشرات الفنية في ترجيح الصعود أو الهبوط للشمعة القادمة."""

    @staticmethod
    def explain(features: list[float], weights: list[float]) -> ExplanationResult:
        if len(features) != len(weights) or len(features) != len(FEATURE_NAMES):
            raise ValueError("أبعاد الميزات والأوزان غير متطابقة مع ميزات النموذج.")

        impacts: list[FeatureImpact] = []
        global_imp: dict[str, float] = {}

        for name, val, w in zip(FEATURE_NAMES, features, weights):
            # المساهمة الموضعية = القيمة * الوزن
            contrib = val * w
            impact_type = "BULLISH" if contrib >= 0 else "BEARISH"
            impacts.append(
                FeatureImpact(
                    name=name,
                    feature_value=val,
                    weight=w,
                    contribution=contrib,
                    impact_type=impact_type,
                )
            )
            # الأهمية الشاملة تعتمد على القيمة المطلقة للوزن
            global_imp[name] = abs(w)

        # فرز العوامل الصاعدة والهابطة بحسب شدة التأثير
        bullish = sorted(
            [f for f in impacts if f.contribution > 0],
            key=lambda f: f.contribution,
            reverse=True,
        )
        bearish = sorted(
            [f for f in impacts if f.contribution < 0],
            key=lambda f: abs(f.contribution),
            reverse=True,
        )

        return ExplanationResult(
            top_bullish_factors=bullish,
            top_bearish_factors=bearish,
            global_importance=global_imp,
        )
