import time
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from core.cache import MemoryCache
from core.candle import Candle
from services.forex_service import ForexService


class TestMemoryCache(unittest.TestCase):
    """اختبارات كاش الذاكرة، الصلاحية، والإحصائيات."""

    def test_cache_set_and_hit(self):
        cache = MemoryCache(default_ttl=10)
        cache.set("test_key", "1.0850")

        val = cache.get("test_key")
        self.assertEqual(val, "1.0850")

        stats = cache.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["items_count"], 1)

    def test_cache_miss_on_unknown_key(self):
        cache = MemoryCache(default_ttl=10)
        val = cache.get("non_existing_key")

        self.assertIsNone(val)
        stats = cache.stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 1)

    def test_cache_expiration(self):
        # كاش ينتهي بعد 0.1 ثانية فقط
        cache = MemoryCache(default_ttl=1)
        cache.set("quick_key", "data", ttl=1)

        self.assertEqual(cache.get("quick_key"), "data")

        # تعيين انتهاء الصلاحية فوراً بالمحاكاة
        cache.store["quick_key"] = ("data", time.time() - 1)

        self.assertIsNone(cache.get("quick_key"))
        stats = cache.stats()
        # الطلب الأول Hit والثاني بعد الانتهاء Miss
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)

    def test_cache_clear(self):
        cache = MemoryCache(default_ttl=10)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        self.assertEqual(cache.stats()["items_count"], 2)

        cache.clear()
        self.assertEqual(cache.stats()["items_count"], 0)
        self.assertIsNone(cache.get("k1"))


class TestForexServiceCacheIntegration(unittest.TestCase):
    """اختبار دمج الكاش في طبقة الخدمة بنمط Cache-Aside."""

    def test_cache_aside_avoids_repeated_api_calls(self):
        mock_source = MagicMock()
        mock_storage = MagicMock()
        mock_candle = Candle(
            pair="EUR/USD",
            timestamp=datetime.now(),
            open=Decimal("1.0800"),
            high=Decimal("1.0850"),
            low=Decimal("1.0790"),
            close=Decimal("1.0825"),
        )
        mock_source.fetch_candles.return_value = [mock_candle]

        test_cache = MemoryCache(default_ttl=60)
        service = ForexService(
            source=mock_source, storage=mock_storage, cache=test_cache
        )

        # 1. الطلب الأول: يجب أن يستدعي الـ API
        price1 = service.get_current_price("EUR/USD")
        self.assertEqual(price1, Decimal("1.0825"))
        self.assertEqual(mock_source.fetch_candles.call_count, 1)

        # 2. الطلب الثاني: يجب أن يأتي من الكاش دون زيادة استدعاء الـ API
        price2 = service.get_current_price("EUR/USD")
        self.assertEqual(price2, Decimal("1.0825"))
        self.assertEqual(mock_source.fetch_candles.call_count, 1)

        # التأكد من عدادات الكاش
        stats = service.get_cache_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)


if __name__ == "__main__":
    unittest.main()
