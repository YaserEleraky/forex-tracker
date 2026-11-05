from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from core.candle import Candle


class Storage(ABC):
    """
    Abstract Base Class تحدد العمليات الأساسية المشتركة لأي نظام تخزين.
    abstract base class that defines the common operations for any storage system.
    """

    @abstractmethod
    def connect(self) -> None:
        """تهيئة وفتح الاتصال بمستودع البيانات.
        This method should establish a connection to the underlying data storage system, preparing it for read/write operations.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """إغلاق الاتصال وتحرير الموارد بأمان.
        This method should close the connection to the underlying data storage system and release any associated resources.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """التحقق من حالة الاتصال الحالية.
        This method should return a boolean indicating whether the storage system is currently connected.
        """
        pass

    @abstractmethod
    def save_candle(self, candle: Candle) -> None:
        """حفظ شمعة سعرية واحدة."""
        pass

    @abstractmethod
    def save_candles_bulk(self, candles: list[Candle]) -> None:
        """حفظ قائمة من الشموع دفعة واحدة بكفاءة داخل Transaction موحدة."""
        pass

    @abstractmethod
    def get_candles(
        self, pair: str, interval: str = "1day", limit: int = 10
    ) -> list[Candle]:
        """استرجاع الشموع لزوج معين وإطار زمني محدد مرتبة زمنياً."""
        pass

    # --- دوال إدارة التنبيهات (Alerts) ---
    @abstractmethod
    def save_alert(self, alert: Any) -> None:
        """حفظ أو تحديث تنبيه في قاعدة البيانات."""
        pass

    @abstractmethod
    def get_alerts(self, active_only: bool = False) -> list[Any]:
        """استرجاع قائمة التنبيهات."""
        pass

    @abstractmethod
    def get_alert_by_id(self, alert_id: str) -> Any | None:
        """استرجاع تنبيه محدد بمعرفه."""
        pass

    @abstractmethod
    def delete_alert(self, alert_id: str) -> bool:
        """حذف تنبيه من قاعدة البيانات."""
        pass
