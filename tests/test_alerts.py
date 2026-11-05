import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from core.alert import Alert, AlertCondition, AlertStatus, ConditionOperator
from core.candle import Candle
from core.exceptions import ValidationError
from services.alert_service import AlertService
from services.forex_service import ForexService
from storage.sqlite_storage import SQLiteStorage


class TestAlertConditionDomain(unittest.TestCase):
    """اختبارات كائنات المجال لشروط التنبيهات."""

    def test_condition_parsing_valid(self):
        c1 = AlertCondition.parse("price > 1.0850")
        self.assertEqual(c1.metric, "price")
        self.assertEqual(c1.operator, ConditionOperator.GREATER_THAN)
        self.assertEqual(c1.target_value, Decimal("1.0850"))

        c2 = AlertCondition.parse("rsi <= 30")
        self.assertEqual(c2.metric, "rsi")
        self.assertEqual(c2.operator, ConditionOperator.LESS_EQUAL)
        self.assertEqual(c2.target_value, Decimal("30"))

    def test_condition_evaluation(self):
        c = AlertCondition.parse("price >= 1.0500")
        self.assertTrue(c.evaluate(Decimal("1.0500")))
        self.assertTrue(c.evaluate(Decimal("1.0501")))
        self.assertFalse(c.evaluate(Decimal("1.0499")))
        self.assertFalse(c.evaluate(None))

    def test_invalid_condition_raises(self):
        with self.assertRaises(ValidationError):
            AlertCondition.parse("price ~ 1.0500")
        with self.assertRaises(ValidationError):
            AlertCondition.parse("price > abc")


class TestAlertStorageAndCRUD(unittest.TestCase):
    """اختبارات استدامة التنبيهات في قاعدة البيانات."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")

    def tearDown(self):
        self.storage.disconnect()

    def test_save_and_retrieve_alert(self):
        cond = AlertCondition.parse("price > 1.1000")
        alert = Alert(pair="EUR/USD", condition=cond, message="Test EUR Alert")
        self.storage.save_alert(alert)

        fetched = self.storage.get_alert_by_id(alert.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.pair, "EUR/USD")
        self.assertEqual(fetched.condition.target_value, Decimal("1.1000"))
        self.assertEqual(fetched.status, AlertStatus.ACTIVE)

    def test_delete_alert(self):
        cond = AlertCondition.parse("price < 1.0000")
        alert = Alert(pair="USD/JPY", condition=cond)
        self.storage.save_alert(alert)

        self.assertTrue(self.storage.delete_alert(alert.id))
        self.assertIsNone(self.storage.get_alert_by_id(alert.id))
        self.assertFalse(self.storage.delete_alert("non_existing_id"))


class TestAlertServiceEvaluation(unittest.TestCase):
    """اختبارات محرك فحص الشروط وتقييم الأسعار والمؤشرات."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")
        self.forex_service = ForexService(storage=self.storage)
        self.alert_service = AlertService(
            storage=self.storage, forex_service=self.forex_service
        )

    def tearDown(self):
        self.storage.disconnect()

    def test_price_alert_trigger(self):
        # 1. إدخال شمعة بسعر إغلاق 1.0950
        candle = Candle(
            pair="EUR/USD",
            interval="1day",
            timestamp=datetime.now(),
            open=Decimal("1.0900"),
            high=Decimal("1.0960"),
            low=Decimal("1.0890"),
            close=Decimal("1.0950"),
        )
        self.storage.save_candle(candle)

        # 2. إنشاء تنبيهين: أحدهما سيتحقق والآخر لن يتحقق
        alert_hit = self.alert_service.create_alert(
            pair="EUR/USD", condition_str="price >= 1.0950"
        )
        alert_miss = self.alert_service.create_alert(
            pair="EUR/USD", condition_str="price > 1.1000"
        )

        # 3. فحص التنبيهات
        triggered = self.alert_service.check_alerts(pair="EUR/USD")

        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["alert_id"], alert_hit.id)
        self.assertEqual(triggered[0]["actual_value"], Decimal("1.0950"))

        # التأكد من تحديث الحالة إلى TRIGGERED في التخزين
        updated = self.storage.get_alert_by_id(alert_hit.id)
        assert updated is not None
        self.assertEqual(updated.status, AlertStatus.TRIGGERED)
        self.assertIsNotNone(updated.triggered_at)

        # التأكد من أن التنبيه الثاني ما زال ACTIVE
        missed = self.storage.get_alert_by_id(alert_miss.id)
        assert missed is not None
        self.assertEqual(missed.status, AlertStatus.ACTIVE)

        # إعادة الفحص مرة أخرى لا يجب أن تطلق التنبيه مجدداً (لأنه أصبح TRIGGERED)
        second_check = self.alert_service.check_alerts(pair="EUR/USD")
        self.assertEqual(len(second_check), 0)


if __name__ == "__main__":
    unittest.main()
