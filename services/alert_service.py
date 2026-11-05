from __future__ import annotations
from decimal import Decimal
from typing import Any

from core.alert import Alert, AlertCondition, AlertStatus
from core.exceptions import ValidationError
from core.intervals import Interval
from core.logger import logger
from core.pair import CurrencyPair
from services.forex_service import ForexService
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


class AlertService:
    """منسق إدارة وتقييم التنبيهات."""

    def __init__(
        self,
        storage: Storage | None = None,
        forex_service: ForexService | None = None,
    ) -> None:
        self.storage = storage or SQLiteStorage()
        self.forex_service = forex_service or ForexService(storage=self.storage)

    def create_alert(
        self,
        pair: str,
        condition_str: str,
        interval: str = "1day",
        message: str = "",
    ) -> Alert:
        """إنشاء وحفظ تنبيه جديد بعد التحقق من صحة المدخلات."""
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)
        condition = AlertCondition.parse(condition_str)

        alert = Alert(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            condition=condition,
            message=message,
        )

        self.storage.save_alert(alert)
        logger.info(
            f"Created alert {alert.id} for {alert.pair} [{alert.interval}]: {condition_str}"
        )
        return alert

    def list_alerts(self, active_only: bool = False) -> list[Alert]:
        """استرجاع قائمة التنبيهات."""
        return self.storage.get_alerts(active_only=active_only)

    def delete_alert(self, alert_id: str) -> bool:
        """حذف تنبيه بواسطة المعرف."""
        success = self.storage.delete_alert(alert_id)
        if success:
            logger.info(f"Deleted alert {alert_id}")
        return success

    def check_alerts(self, pair: str | None = None) -> list[dict[str, Any]]:
        """
        فحص التنبيهات النشطة وتقييمها مقابل أحدث البيانات السعرية والفنية.
        يعيد قائمة بالتنبيهات التي تم إطلاقها (Triggered).
        """
        active_alerts = self.storage.get_alerts(active_only=True)
        if pair:
            target_symbol = CurrencyPair.from_string(pair).symbol
            active_alerts = [a for a in active_alerts if a.pair == target_symbol]

        if not active_alerts:
            return []

        triggered_reports: list[dict[str, Any]] = []

        for alert in active_alerts:
            current_value = self._get_metric_value(alert)

            if current_value is not None and alert.condition.evaluate(current_value):
                # تم تحقق الشرط -> إطلاق التنبيه
                alert.trigger(current_value)
                self.storage.save_alert(alert)

                report = {
                    "alert_id": alert.id,
                    "pair": alert.pair,
                    "interval": alert.interval,
                    "metric": alert.condition.metric,
                    "operator": alert.condition.operator.value,
                    "target_value": alert.condition.target_value,
                    "actual_value": current_value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at,
                }
                triggered_reports.append(report)
                logger.warning(
                    f"🔔 ALERT TRIGGERED [{alert.id}]: {alert.pair} {alert.condition.metric} "
                    f"is {current_value} ({alert.condition.operator.value} {alert.condition.target_value})"
                )

        return triggered_reports

    def _get_metric_value(self, alert: Alert) -> Decimal | None:
        """استخراج القيمة الحالية للمقياس المطلوب من الشموع أو المؤشرات."""
        metric = alert.condition.metric.lower()

        # 1. المقاييس السعرية المباشرة (price, close, open, high, low)
        if metric in ["price", "close", "open", "high", "low"]:
            candles = self.forex_service.get_history(
                pair=alert.pair, interval=alert.interval, limit=1
            )
            if not candles:
                return None
            latest = candles[0]
            if metric in ["price", "close"]:
                return latest.close
            elif metric == "open":
                return latest.open
            elif metric == "high":
                return latest.high
            elif metric == "low":
                return latest.low

        # 2. المقاييس الفنية (RSI, SMA, EMA)
        elif metric in ["rsi", "rsi_14", "sma", "sma_20", "ema", "ema_20"]:
            ind_name = (
                "rsi" if "rsi" in metric else ("sma" if "sma" in metric else "ema")
            )
            report = self.forex_service.analyze_pair(
                pair=alert.pair,
                interval=alert.interval,
                limit=35,
                indicators=[ind_name],
            )
            key_map = {"rsi": "rsi_14", "sma": "sma_20", "ema": "ema_20"}
            target_key = key_map.get(ind_name)

            if target_key and target_key in report["indicators"]:
                results = report["indicators"][target_key]
                if results and results[-1].value is not None:
                    return results[-1].value

        return None
