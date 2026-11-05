"""
core/trade.py
نماذج الصفقات وإشارات التداول (Value Objects & Entities).
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SignalType(str, Enum):
    """إشارات التداول الصادرة من الاستراتيجية."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeStatus(str, Enum):
    """حالة الصفقة في المحاكي."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Trade:
    """كائن يمثل صفقة تداول منفذة في المحاكي."""

    pair: str
    entry_time: datetime
    entry_price: Decimal
    size: Decimal = Decimal("1.0")
    exit_time: datetime | None = None
    exit_price: Decimal | None = None
    status: TradeStatus = TradeStatus.OPEN
    pnl: Decimal = Decimal("0.0")

    def close(self, exit_time: datetime, exit_price: Decimal) -> None:
        """إغلاق الصفقة وحساب الربح أو الخسارة."""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.status = TradeStatus.CLOSED
        # PnL = (سعر الخروج - سعر الدخول) * حجم الصفقة
        self.pnl = (exit_price - self.entry_price) * self.size
