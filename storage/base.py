from __future__ import annotations
from abc import ABC, abstractmethod


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
