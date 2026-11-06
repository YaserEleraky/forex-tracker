import math
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from core.candle import Candle
from core.exceptions import ValidationError
from ml.features import FeatureExtractor
from ml.models.logistic import LogisticForecaster
from services.forecast_service import ForecastService
from storage.sqlite_storage import SQLiteStorage


class TestFeatureExtractor(unittest.TestCase):
    """اختبارات استخراج الميزات الفنية والتحقق من الأبعاد."""

    def test_extract_features_insufficient_candles(self):
        extractor = FeatureExtractor()
        candles = [
            Candle(
                pair="EUR/USD",
                interval="1day",
                timestamp=datetime.now() + timedelta(days=i),
                open=Decimal("1.08"),
                high=Decimal("1.09"),
                low=Decimal("1.07"),
                close=Decimal("1.08"),
            )
            for i in range(20)
        ]
        X, y = extractor.extract_features(candles)
        self.assertEqual(len(X), 0)
        self.assertEqual(len(y), 0)

    def test_extract_features_valid_dimensions(self):
        extractor = FeatureExtractor()
        now = datetime.now()
        candles = []
        for i in range(50):
            delta = math.sin(i * 0.5) * 0.0050
            price = 1.0800 + delta
            candles.append(
                Candle(
                    pair="EUR/USD",
                    interval="1day",
                    timestamp=now + timedelta(days=i),
                    open=Decimal(str(round(price - 0.0005, 5))),
                    high=Decimal(str(round(price + 0.0010, 5))),
                    low=Decimal(str(round(price - 0.0010, 5))),
                    close=Decimal(str(round(price, 5))),
                )
            )

        X, y = extractor.extract_features(candles)
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y))
        # التأكد من احتواء كل عينة على 5 ميزات فنية
        self.assertEqual(len(X[0]), 5)
        # التأكد من أن الأهداف إما 0 أو 1 فقط
        self.assertTrue(all(val in (0, 1) for val in y))


class TestLogisticForecaster(unittest.TestCase):
    """اختبارات تدريب النموذج اللوجستي والتنبؤ الاحتمالي."""

    def test_predict_before_training_raises_error(self):
        model = LogisticForecaster()
        with self.assertRaises(ValidationError):
            model.predict_proba([0.01, 0.02, 0.003, 0.5, 0.001])

    def test_training_and_probability_range(self):
        model = LogisticForecaster()
        # تجهيز عينات تحتوي على الفئتين (0 و 1)
        X = [
            [0.01 * (i % 3), -0.01 * (i % 2), 0.004, 0.5 + (i * 0.01), 0.002]
            for i in range(30)
        ]
        y = [1 if i % 2 == 0 else 0 for i in range(30)]

        metrics = model.train(X, y)
        self.assertTrue(model.is_trained)
        self.assertIn("test_accuracy", metrics)

        sample_features = [0.005, -0.002, 0.003, 0.55, 0.001]
        prob = model.predict_proba(sample_features)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

        direction = model.predict(sample_features)
        self.assertIn(direction, (0, 1))


class TestForecastService(unittest.TestCase):
    """اختبارات تكامل خدمة التنبؤ مع قاعدة البيانات وسلسلة المعالجة."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")
        self.service = ForecastService(storage=self.storage)

    def tearDown(self):
        self.storage.disconnect()

    def test_forecast_insufficient_candles_raises_error(self):
        with self.assertRaises(ValidationError):
            self.service.generate_forecast(pair="EUR/USD", limit=20)

    def test_forecast_pipeline_execution(self):
        now = datetime.now()
        candles = []
        for i in range(80):
            delta = math.sin(i * 0.4) * 0.0050
            price = 1.0800 + delta
            candles.append(
                Candle(
                    pair="EUR/USD",
                    interval="1day",
                    timestamp=now + timedelta(days=i),
                    open=Decimal(str(round(price - 0.0005, 5))),
                    high=Decimal(str(round(price + 0.0010, 5))),
                    low=Decimal(str(round(price - 0.0010, 5))),
                    close=Decimal(str(round(price, 5))),
                )
            )
        self.storage.save_candles_bulk(candles)

        report = self.service.generate_forecast(
            pair="EUR/USD", interval="1day", limit=80
        )
        self.assertEqual(report.pair, "EUR/USD")
        self.assertIn(report.direction, ("UP", "DOWN"))
        self.assertAlmostEqual(
            report.up_probability + report.down_probability, 100.0, places=2
        )
        self.assertGreater(report.train_samples, 0)
        self.assertGreater(report.test_samples, 0)


if __name__ == "__main__":
    unittest.main()
