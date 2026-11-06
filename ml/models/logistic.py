from __future__ import annotations
from typing import Any
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from core.exceptions import ValidationError
from ml.models.base import BaseForecaster


class LogisticForecaster(BaseForecaster):
    """
    نموذج خطي احتمالي لتصنيف حركة السعر القادمة (صعود / هبوط)
    مع قياس دقة التنبؤ على بيانات الاختبار دون تسريب زمني.
    """

    def __init__(self, c_param: float = 1.0, max_iter: int = 200) -> None:
        self.c_param = c_param
        self.max_iter = max_iter
        self.model = LogisticRegression(C=c_param, max_iter=max_iter, random_state=42)
        self.is_trained = False
        self.last_accuracy: float = 0.0

    @property
    def name(self) -> str:
        return "LogisticRegression"

    def train(self, X: list[list[float]], y: list[int]) -> dict[str, float]:
        """
        تدريب النموذج مع تقسيم البيانات زمنياً (80% تدريب و 20% اختبار).
        """
        n_samples = len(X)
        if n_samples < 20:
            raise ValidationError(
                f"عدد العينات المتاحة للتدريب ({n_samples}) غير كافٍ. يلزم 20 عينة على الأقل."
            )

        # تقسيم زمني صارم دون Shuffle
        split_idx = int(n_samples * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # التحقق من وجود كلا الفئتين في بيانات التدريب
        if len(set(y_train)) < 2:
            raise ValidationError(
                f"بيانات التدريب تحتوي على فئة واحدة فقط ({set(y_train)}). "
                "يلزم توفر شموع صاعدة وهابطة معاً. جرب زيادة عدد الشموع (--limit)."
            )

        # تدريب النموذج
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # تقييم الدقة على بيانات الاختبار (Out-of-sample Test)
        y_pred = self.model.predict(X_test)
        self.last_accuracy = float(accuracy_score(y_test, y_pred))

        return {
            "train_samples": float(len(X_train)),
            "test_samples": float(len(X_test)),
            "test_accuracy": round(self.last_accuracy * 100, 2),
        }

    def predict_proba(self, features: list[float]) -> float:
        """
        إرجاع احتمالية الصعود P(Up) للشمعة القادمة.
        """
        if not self.is_trained:
            raise ValidationError("لا يمكن التنبؤ قبل تدريب النموذج أولاً.")

        # predict_proba تعيد مصفوفة [[P(0), P(1)]]
        probs = self.model.predict_proba([features])[0]
        # الاحتمالية الخاصة بالفئة 1 (الصعود)
        return float(probs[1])

    def get_feature_weights(self) -> list[float]:
        """إرجاع أوزان النموذج لكل ميزة (coef_[0]) لاستخدامها في طبقة التفسير."""
        if not self.is_trained:
            raise ValidationError("يجب تدريب النموذج أولاً قبل استخراج الأوزان.")
        return [float(w) for w in self.model.coef_[0]]
