import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from core.candle import Candle
from core.exceptions import ValidationError
from core.intervals import Interval
from core.pair import CurrencyPair
from services.forex_service import ForexService
from storage.sqlite_storage import SQLiteStorage


class TestCurrencyPairAndInterval(unittest.TestCase):
    """اختبارات كائنات المجال للزوج والإطار الزمني."""

    def test_valid_pair_parsing(self):
        p1 = CurrencyPair.from_string("EUR/USD")
        p2 = CurrencyPair.from_string("eurusd")
        p3 = CurrencyPair.from_string("USD_JPY")

        self.assertEqual(p1.symbol, "EUR/USD")
        self.assertEqual(p2.symbol, "EUR/USD")
        self.assertEqual(p3.symbol, "USD/JPY")
        self.assertEqual(p1.base, "EUR")
        self.assertEqual(p1.quote, "USD")

    def test_invalid_pair_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            CurrencyPair.from_string("INVALID_PAIR")

        with self.assertRaises(ValidationError):
            CurrencyPair.from_string("EUR/EUR")  # Base and Quote identical

    def test_interval_aliases_and_validation(self):
        self.assertEqual(Interval.from_str("1h"), Interval.H1)
        self.assertEqual(Interval.from_str("1d"), Interval.D1)
        self.assertEqual(Interval.from_str("15min"), Interval.M15)

        with self.assertRaises(ValueError):
            Interval.from_str("99days")


class TestBulkStorageAndIntervals(unittest.TestCase):
    """اختبارات الحفظ الجماعي وفصل البيانات حسب الإطار الزمني في SQLite."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")

    def tearDown(self):
        self.storage.disconnect()

    def test_bulk_save_and_retrieve_by_interval(self):
        now = datetime(2026, 10, 26, 12, 0)

        # إنشاء شمعتين بنفس التوقيت ولكن بإطارين زمنيين مختلفين
        candle_1d = Candle(
            pair="EUR/USD",
            interval="1day",
            timestamp=now,
            open=Decimal("1.0800"),
            high=Decimal("1.0850"),
            low=Decimal("1.0790"),
            close=Decimal("1.0820"),
            volume=5000,
        )
        candle_1h = Candle(
            pair="EUR/USD",
            interval="1h",
            timestamp=now,
            open=Decimal("1.0810"),
            high=Decimal("1.0830"),
            low=Decimal("1.0805"),
            close=Decimal("1.0825"),
            volume=1200,
        )

        # الحفظ الجماعي
        self.storage.save_candles_bulk([candle_1d, candle_1h])

        # الاسترجاع للإطار اليومي فقط
        daily_res = self.storage.get_candles(pair="EUR/USD", interval="1day", limit=5)
        self.assertEqual(len(daily_res), 1)
        self.assertEqual(daily_res[0].interval, "1day")
        self.assertEqual(daily_res[0].close, Decimal("1.0820"))

        # الاسترجاع لإطار الساعة فقط
        hourly_res = self.storage.get_candles(pair="EUR/USD", interval="1h", limit=5)
        self.assertEqual(len(hourly_res), 1)
        self.assertEqual(hourly_res[0].interval, "1h")
        self.assertEqual(hourly_res[0].close, Decimal("1.0825"))


class TestMultiPairForexService(unittest.TestCase):
    """اختبارات طبقة الخدمة للأزواج المتعددة وقائمة المراقبة دون استدعاء الـ API الخارجي."""

    def setUp(self):
        self.mock_source = MagicMock()
        self.storage = SQLiteStorage(db_path=":memory:")
        # ضبط delay=0 لتسريع الاختبارات
        self.service = ForexService(
            source=self.mock_source, storage=self.storage, rate_limit_delay=0.0
        )

    def tearDown(self):
        self.storage.disconnect()

    def test_fetch_and_store_multiple_pairs(self):
        now = datetime.now()
        fake_eur = Candle(
            pair="EUR/USD",
            interval="1day",
            timestamp=now,
            open=Decimal("1.08"),
            high=Decimal("1.09"),
            low=Decimal("1.07"),
            close=Decimal("1.085"),
        )
        fake_gbp = Candle(
            pair="GBP/USD",
            interval="1day",
            timestamp=now,
            open=Decimal("1.25"),
            high=Decimal("1.26"),
            low=Decimal("1.24"),
            close=Decimal("1.255"),
        )

        # محاكاة ردود الـ source حسب الزوج المطلوب
        def mock_fetch(pair, interval="1day", limit=1):
            if pair == "EUR/USD":
                return [fake_eur]
            elif pair == "GBP/USD":
                return [fake_gbp]
            return []

        self.mock_source.fetch_candles.side_effect = mock_fetch

        results = self.service.fetch_and_store_multiple(
            pairs=["EUR/USD", "GBP/USD"], interval="1day", limit=1
        )

        self.assertIn("EUR/USD", results)
        self.assertIn("GBP/USD", results)
        self.assertEqual(len(results["EUR/USD"]), 1)
        self.assertEqual(len(results["GBP/USD"]), 1)

        # التأكد من التخزين الفعلي لكل زوج
        stored_eur = self.storage.get_candles("EUR/USD", interval="1day")
        stored_gbp = self.storage.get_candles("GBP/USD", interval="1day")
        self.assertEqual(len(stored_eur), 1)
        self.assertEqual(len(stored_gbp), 1)

    def test_get_watchlist(self):
        now = datetime.now()
        fake_candle = Candle(
            pair="USD/JPY",
            interval="1day",
            timestamp=now,
            open=Decimal("150.0"),
            high=Decimal("151.0"),
            low=Decimal("149.5"),
            close=Decimal("150.5"),
        )
        self.mock_source.fetch_candles.return_value = [fake_candle]

        watchlist = self.service.get_watchlist(pairs=["USD/JPY"])
        self.assertEqual(len(watchlist), 1)
        self.assertEqual(watchlist[0]["pair"], "USD/JPY")
        self.assertEqual(watchlist[0]["close"], Decimal("150.5"))


if __name__ == "__main__":
    unittest.main()
