import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from core.candle import Candle
from core.exceptions import ValidationError
from services.forex_service import ForexService
from storage.sqlite_storage import SQLiteStorage


class TestCandleModel(unittest.TestCase):
    """اختبارات منطق الشمعة وقواعد التحقق (Domain Validation)."""

    def test_candle_creation_valid(self):
        c = Candle(
            pair="EUR/USD",
            timestamp=datetime(2026, 10, 25, 12, 0),
            open=Decimal("1.0820"),
            high=Decimal("1.0850"),
            low=Decimal("1.0810"),
            close=Decimal("1.0840"),
            volume=1000,
        )
        self.assertEqual(c.pair, "EUR/USD")
        self.assertEqual(c.close, Decimal("1.0840"))

    def test_candle_invalid_low_greater_than_high(self):
        with self.assertRaises(ValidationError):
            Candle(
                pair="EUR/USD",
                timestamp=datetime.now(),
                open=Decimal("1.0820"),
                high=Decimal("1.0810"),
                low=Decimal("1.0850"),  # Low أعلى من High -> خطأ
                close=Decimal("1.0830"),
            )

    def test_candle_from_dict_and_to_dict(self):
        raw = {
            "symbol": "EUR/USD",
            "datetime": "2026-10-25 14:30:00",
            "open": "1.0820",
            "high": "1.0890",
            "low": "1.0800",
            "close": "1.0875",
            "volume": 250,
        }
        candle = Candle.from_dict(raw)
        self.assertEqual(candle.close, Decimal("1.0875"))

        serialized = candle.to_dict()
        self.assertEqual(serialized["close"], "1.0875")
        self.assertIn("2026-10-25", serialized["timestamp"])


class TestSQLiteStorage(unittest.TestCase):
    """اختبارات التخزين والاسترجاع في قاعدة بيانات SQLite بالذاكرة."""

    def setUp(self):
        # استخدام قاعدة بيانات في الذاكرة لعزل الاختبارات
        self.storage = SQLiteStorage(db_path=":memory:")

    def tearDown(self):
        self.storage.disconnect()

    def test_save_and_get_candles(self):
        c = Candle(
            pair="EUR/USD",
            timestamp=datetime(2026, 10, 25, 10, 0),
            open=Decimal("1.0820"),
            high=Decimal("1.0850"),
            low=Decimal("1.0810"),
            close=Decimal("1.0835"),
            volume=500,
        )
        self.storage.save_candle(c)

        retrieved = self.storage.get_candles(pair="EUR/USD", limit=5)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].close, Decimal("1.0835"))
        self.assertEqual(retrieved[0].pair, "EUR/USD")


class TestForexService(unittest.TestCase):
    """اختبارات طبقة الخدمة وتنسيق العمليات بين الـ API والتخزين."""

    def setUp(self):
        self.mock_source = MagicMock()
        self.storage = SQLiteStorage(db_path=":memory:")
        self.service = ForexService(source=self.mock_source, storage=self.storage)

    def tearDown(self):
        self.storage.disconnect()

    def test_get_current_price(self):
        fake_candle = Candle(
            pair="EUR/USD",
            timestamp=datetime.now(),
            open=Decimal("1.0800"),
            high=Decimal("1.0850"),
            low=Decimal("1.0790"),
            close=Decimal("1.0845"),
        )
        self.mock_source.fetch_candles.return_value = [fake_candle]

        price = self.service.get_current_price("EUR/USD")
        self.assertEqual(price, Decimal("1.0845"))
        self.mock_source.fetch_candles.assert_called_once_with(pair="EUR/USD", limit=1)

    def test_fetch_and_store_orchestration(self):
        fake_candle = Candle(
            pair="EUR/USD",
            timestamp=datetime.now(),
            open=Decimal("1.0800"),
            high=Decimal("1.0850"),
            low=Decimal("1.0790"),
            close=Decimal("1.0825"),
        )
        self.mock_source.fetch_candles.return_value = [fake_candle]

        stored = self.service.fetch_and_store(pair="EUR/USD", limit=1)
        self.assertEqual(len(stored), 1)

        # التحقق من أن الشمعة كُتبت بالفعل داخل التخزين
        history = self.storage.get_candles("EUR/USD", limit=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].close, Decimal("1.0825"))


if __name__ == "__main__":
    unittest.main()
