from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class BaseForecaster(ABC):
    """الواجهة الأساسية لأي نموذج تعلّم آلي يتنبأ باتجاه السعر."""

    @property
    @abstractmethod
    def name(self) -> str:
        """اسم النموذج وخوارزميته."""
        pass

    @abstractmethod
    def train(self, X: list[list[float]], y: list[int]) -> dict[str, float]:
        """
        تدريب النموذج على مصفوفة الميزات X والأهداف y.
        يعيد معايير تقييم الأداء (مثل الدقة Accuracy).
        """
        pass

    @abstractmethod
    def predict_proba(self, features: list[float]) -> float:
        """
        حساب احتمالية أن تكون الشمعة التالية صاعدة (قيمة بين 0.0 و 1.0).
        """
        pass

    def predict(self, features: list[float]) -> int:
        """
        تحديد الاتجاه المتوقع:
        1 = صعود (إذا كانت الاحتمالية >= 0.50)
        0 = هبوط (إذا كانت الاحتمالية < 0.50)
        """
        return 1 if self.predict_proba(features) >= 0.50 else 0
