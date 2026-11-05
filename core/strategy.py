"""
core/strategy.py
العقد التجريدي المشترك لاستراتيجيات التداول.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from core.candle import Candle
from core.trade import SignalType


class BaseStrategy(ABC):
    """الواجهة التجريدية لجميع استراتيجيات التداول."""

    @property
    @abstractmethod
    def name(self) -> str:
        """اسم الاستراتيجية."""
        pass

    @abstractmethod
    def generate_signal(self, index: int, candles: list[Candle]) -> SignalType:
        """
        توليد إشارة تداول (BUY / SELL / HOLD) عند شمعة محددة بناءً على البيانات السابقة فقط.
        """
        pass
