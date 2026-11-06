from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from core.candle import Candle
from core.exceptions import ValidationError
from core.intervals import Interval
from core.logger import logger
from core.pair import CurrencyPair
from ml.features import FeatureExtractor
from ml.models.base import BaseForecaster
from ml.models.logistic import LogisticForecaster
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


@dataclass
class ForecastReport:
    """تقرير التنبؤ بالاتجاه ومؤشرات النموذج الإحصائي."""

    pair: str
    interval: str
    model_name: str
    last_candle_time: str
    latest_close: Decimal
    direction: str  # "UP" أو "DOWN"
    up_probability: float
    down_probability: float
    test_accuracy: float
    train_samples: int
    test_samples: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "interval": self.interval,
            "model_name": self.model_name,
            "last_candle_time": self.last_candle_time,
            "latest_close": float(self.latest_close),
            "direction": self.direction,
            "up_probability": round(self.up_probability, 2),
            "down_probability": round(self.down_probability, 2),
            "test_accuracy": round(self.test_accuracy, 2),
            "train_samples": self.train_samples,
            "test_samples": self.test_samples,
        }


class ForecastService:
    """منسق خط تدريب نماذج التعلّم الآلي والتنبؤ اللحظي."""

    def __init__(
        self,
        storage: Storage | None = None,
        extractor: FeatureExtractor | None = None,
        model: BaseForecaster | None = None,
    ) -> None:
        self.storage = storage or SQLiteStorage()
        self.extractor = extractor or FeatureExtractor()
        self.model = model or LogisticForecaster()

    def generate_forecast(
        self,
        pair: str = "EUR/USD",
        interval: str = "1day",
        limit: int = 150,
    ) -> ForecastReport:
        """
        جلب الشموع وتدريب النموذج وحساب احتمالية اتجاه الشمعة القادمة.
        """
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)

        candles = self.storage.get_candles(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            limit=limit,
        )

        min_candles_needed = 60
        if len(candles) < min_candles_needed:
            raise ValidationError(
                f"البيانات المخزنة لزوج {validated_pair.symbol} ({len(candles)} شمعة) غير كافية لتدريب النموذج. "
                f"يلزم توفر {min_candles_needed} شمعة على الأقل.\n"
                f"استخدم أولاً: forex fetch --pair {validated_pair.symbol} --interval {validated_interval.value} --limit {limit}"
            )

        candles_sorted = sorted(candles, key=lambda c: c.timestamp)

        # 1. استخراج مصفوفات الميزات والأهداف التاريخية
        X, y = self.extractor.extract_features(candles_sorted)
        if len(X) < 20:
            raise ValidationError("تعذر استخراج عينات كافية بعد حساب المؤشرات الفنية.")

        # 2. تدريب النموذج وتقييم الدقة
        metrics = self.model.train(X, y)

        # 3. استخراج ميزات الشمعة الأخيرة الحالية
        latest_features = self.extractor.extract_latest_features(candles_sorted)
        if latest_features is None:
            raise ValidationError("تعذر استخراج ميزات الشمعة الحالية لتوليد التنبؤ.")

        # 4. حساب الاحتمالية وتحديد الاتجاه
        up_prob = self.model.predict_proba(latest_features) * 100.0
        down_prob = 100.0 - up_prob
        direction = "UP" if up_prob >= 50.0 else "DOWN"

        last_candle = candles_sorted[-1]

        logger.info(
            f"Forecast generated for {validated_pair.symbol} [{validated_interval.value}]: "
            f"Direction={direction}, P(Up)={up_prob:.1f}%, TestAcc={metrics['test_accuracy']}%"
        )

        return ForecastReport(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            model_name=self.model.name,
            last_candle_time=last_candle.timestamp.strftime("%Y-%m-%d %H:%M"),
            latest_close=last_candle.close,
            direction=direction,
            up_probability=up_prob,
            down_probability=down_prob,
            test_accuracy=metrics["test_accuracy"],
            train_samples=int(metrics["train_samples"]),
            test_samples=int(metrics["test_samples"]),
        )
