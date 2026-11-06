"""
tests/test_risk.py
Automated unit tests for risk management and position sizing (Sprint 10).
"""
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from core.exceptions import ValidationError
from core.risk import RiskCalculator
from services.risk_service import RiskService


class TestRiskCalculator(unittest.TestCase):
    """Test pip scale, lot sizes, and boundary conditions."""

    def test_pip_size_detection(self):
        self.assertEqual(RiskCalculator.get_pip_size("EUR/USD"), Decimal("0.0001"))
        self.assertEqual(RiskCalculator.get_pip_size("USD/JPY"), Decimal("0.01"))
        self.assertEqual(RiskCalculator.get_pip_size("EUR_JPY"), Decimal("0.01"))

    def test_pips_calculation(self):
        pips = RiskCalculator.calculate_pips("EUR/USD", Decimal("1.0850"), Decimal("1.0820"))
        self.assertEqual(pips, Decimal("30.0"))

        jpy_pips = RiskCalculator.calculate_pips("USD/JPY", Decimal("155.50"), Decimal("155.00"))
        self.assertEqual(jpy_pips, Decimal("50.0"))

    def test_position_sizing_standard_pair(self):
        plan = RiskCalculator.compute_position_size(
            pair="EUR/USD",
            account_balance=Decimal("10000.00"),
            risk_percentage=Decimal("1.0"),
            entry_price=Decimal("1.1000"),
            stop_loss_price=Decimal("1.0950"),
            take_profit_price=Decimal("1.1100"),
        )

        self.assertEqual(plan.risk_amount, Decimal("100.00"))
        self.assertEqual(plan.stop_loss_pips, Decimal("50.0"))
        self.assertEqual(plan.take_profit_pips, Decimal("100.0"))
        self.assertEqual(plan.risk_reward_ratio, Decimal("2.00"))
        self.assertEqual(plan.standard_lots, Decimal("0.20"))
        self.assertEqual(plan.mini_lots, Decimal("2.0"))
        self.assertEqual(plan.micro_lots, Decimal("20"))
        self.assertEqual(plan.units, 20000)

    def test_invalid_parameters_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            RiskCalculator.compute_position_size(
                pair="EUR/USD",
                account_balance=Decimal("-100"),
                risk_percentage=Decimal("1.0"),
                entry_price=Decimal("1.10"),
                stop_loss_price=Decimal("1.09"),
            )
        with self.assertRaises(ValidationError):
            RiskCalculator.compute_position_size(
                pair="EUR/USD",
                account_balance=Decimal("10000"),
                risk_percentage=Decimal("105.0"),
                entry_price=Decimal("1.10"),
                stop_loss_price=Decimal("1.09"),
            )
        with self.assertRaises(ValidationError):
            RiskCalculator.compute_position_size(
                pair="EUR/USD",
                account_balance=Decimal("10000"),
                risk_percentage=Decimal("1.0"),
                entry_price=Decimal("1.10"),
                stop_loss_price=Decimal("1.10"),
            )


class TestRiskService(unittest.TestCase):
    """Test service orchestration and fallback to live market prices."""

    def test_calculate_plan_derives_stop_loss_from_pips(self):
        mock_forex = MagicMock()
        mock_forex.get_current_price.return_value = Decimal("1.1000")
        service = RiskService(forex_service=mock_forex)

        plan = service.calculate_plan(
            pair="EUR/USD",
            account_balance=Decimal("5000"),
            risk_pct=Decimal("2.0"),
            entry=Decimal("1.1000"),
            sl_pips=Decimal("25.0"),
            tp_pips=Decimal("50.0"),
        )

        self.assertEqual(plan.stop_loss_pips, Decimal("25.0"))
        self.assertEqual(plan.take_profit_pips, Decimal("50.0"))
        self.assertEqual(plan.risk_reward_ratio, Decimal("2.00"))
        self.assertEqual(plan.standard_lots, Decimal("0.40"))


if __name__ == "__main__":
    unittest.main()
