from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from core.exceptions import ValidationError


class AlertStatus(str, Enum):
    """حالات التنبيه."""

    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    DISABLED = "DISABLED"


class ConditionOperator(str, Enum):
    """معاملات المقارنة المدعومة."""

    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="

    @classmethod
    def from_str(cls, op_str: str) -> ConditionOperator:
        for op in cls:
            if op.value == op_str.strip():
                return op
        raise ValidationError(f"معامل مقارنة غير مدعوم: {op_str}")


@dataclass(frozen=True)
class AlertCondition:
    """كائن يمثل شرط التنبيه (مثال: price > 1.0850 أو rsi < 30)."""

    metric: str  # 'price', 'rsi', 'sma', etc.
    operator: ConditionOperator
    target_value: Decimal

    @classmethod
    def parse(cls, condition_str: str) -> AlertCondition:
        """تحليل نص الشرط بأمان (مثل: 'price > 1.0900' أو 'rsi <= 30')."""
        operators = [">=", "<=", "==", ">", "<"]
        matched_op = None
        for op in operators:
            if op in condition_str:
                matched_op = op
                break

        if not matched_op:
            raise ValidationError(
                f"صيغة الشرط غير صحيحة: '{condition_str}'. يجب أن يحتوي على أحد المعاملات: >, >=, <, <=, =="
            )

        parts = condition_str.split(matched_op, 1)
        metric = parts[0].strip().lower()
        raw_val = parts[1].strip()

        if not metric:
            raise ValidationError("اسم المقياس مفقود في الشرط.")

        try:
            target_val = Decimal(raw_val)
        except Exception as err:
            raise ValidationError(
                f"القيمة المستهدفة في الشرط غير صالحة: '{raw_val}'"
            ) from err

        return cls(
            metric=metric,
            operator=ConditionOperator.from_str(matched_op),
            target_value=target_val,
        )

    def evaluate(self, current_value: Decimal | None) -> bool:
        """تقييم الشرط مقابل القيمة الحالية."""
        if current_value is None:
            return False

        if self.operator == ConditionOperator.GREATER_THAN:
            return current_value > self.target_value
        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return current_value >= self.target_value
        elif self.operator == ConditionOperator.LESS_THAN:
            return current_value < self.target_value
        elif self.operator == ConditionOperator.LESS_EQUAL:
            return current_value <= self.target_value
        elif self.operator == ConditionOperator.EQUAL:
            return current_value == self.target_value
        return False


@dataclass
class Alert:
    """كائن التنبيه المالي."""

    pair: str
    condition: AlertCondition
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    interval: str = "1day"
    status: AlertStatus = AlertStatus.ACTIVE
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    triggered_at: datetime | None = None

    def __post_init__(self) -> None:
        self.pair = self.pair.upper()
        if not self.message:
            self.message = f"تنبيه {self.pair}: تحقق الشرط {self.condition.metric} {self.condition.operator.value} {self.condition.target_value}"

    def trigger(self, current_val: Decimal) -> None:
        """تغيير حالة التنبيه إلى تم الإطلاق وتوثيق التوقيت."""
        self.status = AlertStatus.TRIGGERED
        self.triggered_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """تحويل التنبيه إلى قاموس لتسهيل التخزين والنقل."""
        return {
            "id": self.id,
            "pair": self.pair,
            "interval": self.interval,
            "metric": self.condition.metric,
            "operator": self.condition.operator.value,
            "target_value": str(self.condition.target_value),
            "status": self.status.value,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "triggered_at": (
                self.triggered_at.isoformat() if self.triggered_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alert:
        """إنشاء كائن Alert من قاموس قاعدة البيانات."""
        condition = AlertCondition(
            metric=data["metric"],
            operator=ConditionOperator.from_str(data["operator"]),
            target_value=Decimal(str(data["target_value"])),
        )
        return cls(
            id=data["id"],
            pair=data["pair"],
            interval=data.get("interval", "1day"),
            condition=condition,
            status=AlertStatus(data.get("status", "ACTIVE")),
            message=data.get("message", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            triggered_at=(
                datetime.fromisoformat(data["triggered_at"])
                if data.get("triggered_at")
                else None
            ),
        )
