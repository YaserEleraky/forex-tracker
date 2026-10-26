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
    """محرك تخزين SQLite يدعم العمليات الدفعية والفهارس المركبة."""

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
                logger.info(f"Connected to SQLite database at: {self.db_path}")
        except sqlite3.Error as err:
            logger.error(f"Failed to connect to SQLite: {err}")
            raise StorageError(f"SQLite Connection Error: {err}") from err

    def disconnect(self) -> None:
        if self.is_connected() and self._connection:
            self._connection.close()
            self._connection = None
            logger.info("SQLite connection closed.")

    def is_connected(self) -> bool:
        return self._connection is not None

    def _init_db(self) -> None:
        """إنشاء جدول الشموع والفهارس المركبة مع معالجة الترحيل التلقائي."""
        if not self._connection:
            self.connect()

        try:
            cursor = self._connection.cursor()

            # 1. إنشاء الجدول بالمخطط الجديد إن لم يكن موجوداً
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS candles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        interval TEXT NOT NULL DEFAULT '1day',
                        timestamp TEXT NOT NULL,
                        open TEXT NOT NULL,
                        high TEXT NOT NULL,
                        low TEXT NOT NULL,
                        close TEXT NOT NULL,
                        volume INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(pair, interval, timestamp) ON CONFLICT REPLACE
                    )
                """)

            # 2. فحص الأعمدة الحالية (Schema Migration)
            cursor.execute("PRAGMA table_info(candles)")
            existing_columns = [row["name"] for row in cursor.fetchall()]

            # إضافة عمود interval تلقائياً إذا كانت قاعدة البيانات قديمة من Sprint 1
            if "interval" not in existing_columns:
                cursor.execute(
                    "ALTER TABLE candles ADD COLUMN interval TEXT NOT NULL DEFAULT '1day'"
                )
                logger.info(
                    "تم ترحيل المخطط بنجاح: إضافة عمود 'interval' إلى جدول candles."
                )

            # 3. إنشاء الفهرس المركب
            cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pair_interval_timestamp
                    ON candles (pair, interval, timestamp DESC)
                """)

            self._connection.commit()
        except sqlite3.Error as err:
            logger.error(f"Failed to initialize SQLite schema: {err}")
            raise StorageError(f"Database schema initialization error: {err}") from err

    def save_candle(self, candle: Candle) -> None:
        """حفظ شمعة مفردة بالاعتماد على دالة الحفظ الجماعي."""
        self.save_candles_bulk([candle])

    def save_candles_bulk(self, candles: list[Candle]) -> None:
        """
        حفظ مجموعة شموع دفعة واحدة باستخدام executemany لتحقيق سرعة كتابة قصوى.
        """
        if not candles:
            return

        if not self.is_connected():
            self.connect()

        query = """
            INSERT OR REPLACE INTO candles (pair, interval, timestamp, open, high, low, close, volume)
            VALUES (:pair, :interval, :timestamp, :open, :high, :low, :close, :volume)
        """
        records = [c.to_dict() for c in candles]

        try:
            cursor = self._connection.cursor()
            cursor.executemany(query, records)
            self._connection.commit()
            logger.info(f"Saved {len(candles)} candle(s) to SQLite.")
        except sqlite3.Error as err:
            logger.error(f"Failed bulk inserting candles: {err}")
            raise StorageError(f"Bulk insert failed: {err}") from err

    def get_candles(
        self, pair: str, interval: str = "1day", limit: int = 10
    ) -> list[Candle]:
        """استرجاع أحدث الشموع لزوج وإطار زمني محدد."""
        if not self.is_connected():
            self.connect()

        query = """
            SELECT pair, interval, timestamp, open, high, low, close, volume
            FROM candles
            WHERE pair = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, (pair.upper(), interval, limit))
            rows = cursor.fetchall()

            candles: list[Candle] = []
            for row in rows:
                row_dict = dict(row)
                row_dict["datetime"] = row_dict.pop("timestamp")
                candles.append(Candle.from_dict(row_dict))

            return candles
        except sqlite3.Error as err:
            logger.error(f"Failed retrieving candles: {err}")
            raise StorageError(f"Query candles failed: {err}") from err
