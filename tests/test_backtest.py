import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from core.candle import Candle
from core.exceptions import ValidationError
from core.trade import SignalType, Trade, TradeStatus
from services.backtest_service import BacktestService
from storage.sqlite_storage import SQLiteStorage
from strategies.sma_crossover import SMACrossoverStrategy


class TestTradeEntity(unittest.TestCase):
    """اختبارات كائن الصفقة وحساب الأرباح والخسائر."""

    def test_trade_close_profit(self):
        trade = Trade(
            pair="EUR/USD",
            entry_time=datetime(2026, 1, 1, 10, 0),
            entry_price=Decimal("1.0800"),
            size=Decimal("10000.0"),
        )
        trade.close(
            exit_time=datetime(2026, 1, 2, 10, 0),
            exit_price=Decimal("1.0900"),
        )
        self.assertEqual(trade.status, TradeStatus.CLOSED)
        # PnL = (1.0900 - 1.0800) * 10000 = 100.00
        self.assertEqual(trade.pnl, Decimal("100.0000"))

    def test_trade_close_loss(self):
        trade = Trade(
            pair="EUR/USD",
            entry_time=datetime(2026, 1, 1, 10, 0),
            entry_price=Decimal("1.0800"),
            size=Decimal("10000.0"),
        )
        trade.close(
            exit_time=datetime(2026, 1, 2, 10, 0),
            exit_price=Decimal("1.0750"),
        )
        self.assertEqual(trade.status, TradeStatus.CLOSED)
        # PnL = (1.0750 - 1.0800) * 10000 = -50.00
        self.assertEqual(trade.pnl, Decimal("-50.0000"))


class TestSMACrossoverStrategy(unittest.TestCase):
    """اختبارات استراتيجية تقاطع المتوسطات وتوليد الإشارات."""

    def test_invalid_periods_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            SMACrossoverStrategy(fast_period=20, slow_period=10)
        with self.assertRaises(ValidationError):
            SMACrossoverStrategy(fast_period=15, slow_period=15)

    def test_generate_signal_hold_when_insufficient_candles(self):
        strategy = SMACrossoverStrategy(fast_period=3, slow_period=5)
        now = datetime.now()
        candles = [
            Candle(
                pair="EUR/USD",
                interval="1day",
                timestamp=now + timedelta(days=i),
                open=Decimal("1.08"),
                high=Decimal("1.09"),
                low=Decimal("1.07"),
                close=Decimal("1.08"),
            )
            for i in range(4)
        ]
        # index < slow_period (4 < 5)
        signal = strategy.generate_signal(3, candles)
        self.assertEqual(signal, SignalType.HOLD)


class TestBacktestService(unittest.TestCase):
    """اختبارات محاكي التداول ومقاييس الأداء المالي."""

    def setUp(self):
        self.storage = SQLiteStorage(db_path=":memory:")
        self.service = BacktestService(storage=self.storage)

    def tearDown(self):
        self.storage.disconnect()

    def test_backtest_no_candles_raises_error(self):
        strategy = SMACrossoverStrategy(fast_period=3, slow_period=5)
        with self.assertRaises(ValidationError):
            self.service.run(strategy=strategy, pair="EUR/USD", limit=50)

    def test_backtest_execution_flow_and_metrics(self):
        # محاكاة حركة أسعار تولد إشارة شراء ثم إشارة بيع
        prices = [
            1.0500,
            1.0500,
            1.0500,
            1.0500,
            1.0500,
            1.0500,  # ثبات
            1.0400,
            1.0300,
            1.0200,  # هبوط
            1.0400,
            1.0600,
            1.0800,  # صعود حاد -> تقاطع صاعد (BUY)
            1.0700,
            1.0500,
            1.0300,  # هبوط -> تقاطع هابط (SELL)
        ]
        start_date = datetime(2026, 1, 1)
        candles = [
            Candle(
                pair="EUR/USD",
                interval="1day",
                timestamp=start_date + timedelta(days=i),
                open=Decimal(str(p)),
                high=Decimal(str(p + 0.0010)),
                low=Decimal(str(p - 0.0010)),
                close=Decimal(str(p)),
            )
            for i, p in enumerate(prices)
        ]
        self.storage.save_candles_bulk(candles)

        strategy = SMACrossoverStrategy(fast_period=2, slow_period=5)
        result = self.service.run(
            strategy=strategy,
            pair="EUR/USD",
            limit=len(candles),
            initial_capital=Decimal("10000.0"),
            trade_size=Decimal("10000.0"),
        )

        self.assertGreater(result.total_trades, 0)
        self.assertIsInstance(result.roi_percent, float)
        self.assertIsInstance(result.max_drawdown_percent, float)
        self.assertGreaterEqual(result.win_rate, 0.0)
        self.assertLessEqual(result.win_rate, 100.0)
        self.assertEqual(result.pair, "EUR/USD")
        self.assertEqual(result.strategy_name, strategy.name)


if __name__ == "__main__":
    unittest.main()
