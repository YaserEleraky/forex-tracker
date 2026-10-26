from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from core.exceptions import ValidationError


@dataclass(frozen=True)
class Candle:
    """
    this class represents a single candle in a candlestick chart, which is commonly used in financial markets to represent price movements over a specific time period.
    Attributes:
        pair (str): The currency pair or asset symbol (e.g., "EUR/USD").
        timestamp (datetime): The timestamp of the candle.
        open (Decimal): The opening price of the candle.
        high (Decimal): The highest price of the candle.
        low (Decimal): The lowest price of the candle.
        close (Decimal): The closing price of the candle.
        volume (int): The trading volume during the candle's time period (default is 0
    this Value object is immutable, meaning that once it is created, its attributes cannot be changed. This is achieved by using the @dataclass decorator with the frozen=True parameter.
    The __post_init__ method is used to perform validation checks on the attributes after the object
    """

    pair: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = 0
    interval: str = "1day"

    def __post_init__(self):
        if not self.pair:
            raise ValidationError("Pair cannot be empty.")
        if self.low > self.high:
            raise ValidationError(
                f"({self.low}) low cannot be greater than high ({self.high})."
            )
        if (
            self.open < Decimal("0")
            or self.high < Decimal("0")
            or self.low < Decimal("0")
            or self.close < Decimal("0")
        ):
            raise ValidationError("Price values cannot be negative.")
        if self.volume < 0:
            raise ValidationError("Volume cannot be negative.")
        if not isinstance(self.timestamp, datetime):
            raise ValidationError("Timestamp must be a datetime object.")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candle:
        """
        Factory Method لإنشاء كائن Candle من قاموس (سواء من الـ API أو قاعدة البيانات).
        يدعم جميع صيغ ISO 8601 (بمسافة أو بحرف T أو تاريخ فقط).
        """
        try:
            raw_ts = data["datetime"]
            if isinstance(raw_ts, datetime):
                ts = raw_ts
            elif isinstance(raw_ts, str):
                # استبدال المسافة بحرف T لتوحيد الصيغة المعيارية ISO ثم القراءة المباشرة
                normalized_ts = raw_ts.replace(" ", "T")
                ts = datetime.fromisoformat(normalized_ts)
            else:
                raise ValueError(f"صيغة تاريخ غير مدعومة: {raw_ts}")

            return cls(
                pair=data.get("symbol", data.get("pair", "EUR/USD")).upper(),
                timestamp=ts,
                open=Decimal(str(data["open"])),
                high=Decimal(str(data["high"])),
                low=Decimal(str(data["low"])),
                close=Decimal(str(data["close"])),
                volume=int(data.get("volume", 0)),
                interval=str(data.get("interval", "1day")),
            )
        except (KeyError, ValueError) as err:
            raise ValidationError(f"فشل إنشاء الشمعة من البيانات: {err}") from err

    def to_dict(self) -> dict[str, Any]:
        """تحويل الشمعة إلى قاموس لحفظها أو تصديرها بسهولة.
        Convert the candle to a dictionary for easy storage or export.
        """
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat(),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": self.volume,
            "interval": self.interval,
        }
