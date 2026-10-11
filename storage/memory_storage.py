"""
storage/memory_storage.py
تطبيق عقد التخزين في الذاكرة (In-Memory) للاختبارات والتطوير الأولي.
"""

from __future__ import annotations
from typing import Any
from storage.base import Storage
from core.logger import logger


class MemoryStorage(Storage):
    """
    تخزين داخلي في الذاكرة عبر هياكل بيانات Python.
    This class implements an in-memory storage system using Python's built-in data structures.
    """

    def __init__(self) -> None:
        """
        Initialize the in-memory storage system.
        This constructor sets up the internal data structures and connection state.
        """
        self._connected: bool = False
        self._data: dict[str, Any] = {}

    def connect(self) -> None:
        """
        Connect to the in-memory storage system.
        This method establishes a connection to the in-memory storage system, preparing it for read/write operations.
        """
        self._connected = True
        logger.info("MemoryStorage connected.")

    def disconnect(self) -> None:
        """
        Disconnect from the in-memory storage system.
        This method closes the connection to the in-memory storage system and releases any associated resources.
        """
        self._connected = False
        self._data.clear()
        logger.info("MemoryStorage disconnected.")

    def is_connected(self) -> bool:
        """
        Check the current connection status.
        This method returns a boolean indicating whether the storage system is currently connected.
        """
        return self._connected
