"""
core/cache.py
نظام كاش مبسط يدعم الذاكرة المحلية (Memory) وخادم (Redis) مع التبديل التلقائي.
"""

from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from core.config import Config
from core.logger import logger


# ==========================================================
# 1. الواجهة المشتركة (العقد الأساسي)
# ==========================================================
class BaseCache(ABC):
    """أي كاش سنبنيه يجب أن يحتوي على هذه الدوال الأربع فقط."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """جلب القيمة بواسطة المفتاح."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """تخزين القيمة مع تحديد مدة الصلاحية بالثواني."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """مسح كل محتويات الكاش."""
        pass

    @abstractmethod
    def stats(self) -> dict[str, Any]:
        """عرض إحصائيات بسيطة (كم مرة وفرنا طلب للشبكة)."""
        pass


# ==========================================================
# 2. كاش الذاكرة العادية (Memory Cache)
# ==========================================================
class MemoryCache(BaseCache):
    """كاش محلي بسيط يعتمد على قاموس بايثون (dict)."""

    def __init__(self, default_ttl: int = 60) -> None:
        # القاموس يخزن: key -> (value, وقت الانتهاء)
        self.store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        if key not in self.store:
            self.misses += 1
            return None

        val, expires_at = self.store[key]

        # فحص انتهاء الوقت
        if time.time() > expires_at:
            del self.store[key]
            self.misses += 1
            return None

        self.hits += 1
        return val

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        seconds = ttl if ttl is not None else self.default_ttl
        expire_time = time.time() + seconds
        self.store[key] = (value, expire_time)

    def clear(self) -> None:
        self.store.clear()

    def stats(self) -> dict[str, Any]:
        return {
            "backend": "memory",
            "hits": self.hits,
            "misses": self.misses,
            "items_count": len(self.store),
        }


# ==========================================================
# 3. كاش خادم ريديس (Redis Cache)
# ==========================================================
class RedisCache(BaseCache):
    """تخزين مؤقت عبر خادم Redis خارجي مع عدادات مستمرة."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 60
    ) -> None:
        import redis

        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.client.ping()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        try:
            val = self.client.get(key)
            if val is None:
                self.client.incr("forex:stats:misses")
                return None

            self.client.incr("forex:stats:hits")
            try:
                return json.loads(val)
            except (ValueError, TypeError):
                return val
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        seconds = ttl if ttl is not None else self.default_ttl
        try:
            raw_data = (
                json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            )
            self.client.setex(key, seconds, raw_data)
        except Exception as err:
            logger.warning(f"Failed to write to Redis for key {key}: {err}")

    def clear(self) -> None:
        try:
            self.client.flushdb()
        except Exception:
            pass

    def stats(self) -> dict[str, Any]:
        try:
            hits = int(self.client.get("forex:stats:hits") or 0)
            misses = int(self.client.get("forex:stats:misses") or 0)
            keys_count = self.client.dbsize()
        except Exception:
            hits, misses, keys_count = 0, 0, 0

        return {
            "backend": "redis",
            "hits": hits,
            "misses": misses,
            "items_count": keys_count,
        }


# ==========================================================
# 4. دالة المصنع وتحديد الكاش (Factory Function)
# ==========================================================
def get_cache() -> BaseCache:
    """
    تختار الكاش المناسب تلقائياً من ملف الإعدادات:
    إذا اخترت 'redis' وفشل الاتصال، تعود لـ 'memory' بسلاسة.
    """
    cfg = Config().get("cache", {})
    backend = cfg.get("backend", "memory").lower()
    default_ttl = cfg.get("default_ttl", 60)
    redis_url = cfg.get("redis_url", "redis://localhost:6379/0")

    if backend == "redis":
        try:
            return RedisCache(redis_url=redis_url, default_ttl=default_ttl)
        except Exception as err:
            logger.warning(
                f"Redis is not available ({err}). Falling back to MemoryCache."
            )

    return MemoryCache(default_ttl=default_ttl)
