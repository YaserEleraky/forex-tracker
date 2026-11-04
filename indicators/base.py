from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from core.candle import Candle


@dataclass(frozen=True)
class IndicatorResult:

    name: str
    timestamp: Any
    value: Decimal | None
    extra: dict[str, Any] | None = None


class BaseIndicator(ABC):
    """
    Abstract base class for all indicators.
    """

    @abstractmethod
    def calculate(self, candles: list[Candle]) -> list[IndicatorResult]:
        """
        Calculate the indicator value based on the provided candles.
        """
        pass
