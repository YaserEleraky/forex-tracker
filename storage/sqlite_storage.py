from __future__ import annotations
import os
import sqlite3
from datetime import datetime
from decimal import Decimal
from core.candle import Candle
from core.config import Config
from core.exceptions import StorageError
from core.logger import logger
from storage.base import Storage


class SQLiteStorage(Storage):
    """محرك تخزين يعتمد على SQLite لحفظ الشموع بدقة متناهية."""

    def __init__(self, db_path: str | None = None) -> None:
        config = Config()
        default_dir = config.get("data_dir", "./data")
        os.makedirs(default_dir, exist_ok=True)

        self.db_path = db_path or os.path.join(default_dir, "candles.db")
        self._connection: sqlite3.Connection | None = None
        self.connect()
        self._init_db()

    def connect(self) -> None:
        try:
            if not self.is_connected():
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
                logger.info(f"تم فتح الاتصال بقاعدة SQLite: {self.db_path}")
        except sqlite3.Error as err:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {err}")
            raise StorageError(f"خطأ اتصال SQLite: {err}") from err

    def disconnect(self) -> None:
        if self.is_connected() and self._connection:
            self._connection.close()
            self._connection = None
            logger.info("تم إغلاق اتصال SQLite بنجاح.")

    def is_connected(self) -> bool:
        return self._connection is not None

    def _init_db(self) -> None:
        if not self._connection:
            self.connect()

        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pair TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open TEXT NOT NULL,
                    high TEXT NOT NULL,
                    low TEXT NOT NULL,
                    close TEXT NOT NULL,
                    volume INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(pair, timestamp) ON CONFLICT REPLACE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pair_timestamp
                ON candles (pair, timestamp DESC)
            """)
            self._connection.commit()
        except sqlite3.Error as err:
            logger.error(f"فشل تهيئة جداول SQLite: {err}")
            raise StorageError(f"خطأ تهيئة الجدول: {err}") from err

    def save_candle(self, candle: Candle) -> None:
        if not self.is_connected():
            self.connect()

        data = candle.to_dict()
        query = """
            INSERT OR REPLACE INTO candles (pair, timestamp, open, high, low, close, volume)
            VALUES (:pair, :timestamp, :open, :high, :low, :close, :volume)
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, data)
            self._connection.commit()
            logger.info(f"تم حفظ شمعة {candle.pair} في SQLite.")
        except sqlite3.Error as err:
            logger.error(f"فشل حفظ الشمعة: {err}")
            raise StorageError(f"خطأ حفظ الشمعة: {err}") from err

    def get_candles(self, pair: str, limit: int = 10) -> list[Candle]:
        if not self.is_connected():
            self.connect()

        query = """
            SELECT pair, timestamp, open, high, low, close, volume
            FROM candles
            WHERE pair = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, (pair.upper(), limit))
            rows = cursor.fetchall()

            candles: list[Candle] = []
            for row in rows:
                row_dict = dict(row)
                row_dict["datetime"] = row_dict.pop("timestamp")
                candles.append(Candle.from_dict(row_dict))

            return candles
        except sqlite3.Error as err:
            logger.error(f"فشل قراءة الشموع: {err}")
            raise StorageError(f"خطأ استرجاع الشموع: {err}") from err
