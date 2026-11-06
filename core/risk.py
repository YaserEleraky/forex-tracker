"""
core/risk.py
Domain entities and calculations for position sizing and risk management.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from core.exceptions import ValidationError


@dataclass(frozen=True)
class RiskPlan:
    """Calculated position sizing and trade risk evaluation."""
    pair: str
    account_balance: Decimal
    risk_percentage: Decimal
    risk_amount: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal | None
    stop_loss_pips: Decimal
    take_profit_pips: Decimal | None
    risk_reward_ratio: Decimal | None
    pip_value_per_standard_lot: Decimal
    units: int
    standard_lots: Decimal
    mini_lots: Decimal
    micro_lots: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "account_balance": float(self.account_balance),
            "risk_percentage": float(self.risk_percentage),
            "risk_amount": float(self.risk_amount),
            "entry_price": float(self.entry_price),
            "stop_loss_price": float(self.stop_loss_price),
            "take_profit_price": float(self.take_profit_price) if self.take_profit_price else None,
            "stop_loss_pips": float(self.stop_loss_pips),
            "take_profit_pips": float(self.take_profit_pips) if self.take_profit_pips else None,
            "risk_reward_ratio": float(self.risk_reward_ratio) if self.risk_reward_ratio else None,
            "units": self.units,
            "standard_lots": float(self.standard_lots),
            "mini_lots": float(self.mini_lots),
            "micro_lots": float(self.micro_lots),
        }


class RiskCalculator:
    """Pure mathematical engine for FX pip values and lot calculations."""

    @staticmethod
    def get_pip_size(pair: str) -> Decimal:
        """Return pip decimal scale: 0.01 for JPY quotes, 0.0001 for all others."""
        normalized = pair.upper().replace("/", "").replace("_", "")
        if "JPY" in normalized:
            return Decimal("0.01")
        return Decimal("0.0001")

    @classmethod
    def calculate_pips(cls, pair: str, price_a: Decimal, price_b: Decimal) -> Decimal:
        """Calculate absolute difference between two prices in pips."""
        pip_size = cls.get_pip_size(pair)
        diff = abs(price_a - price_b)
        return (diff / pip_size).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    @classmethod
    def compute_position_size(
        cls,
        pair: str,
        account_balance: Decimal,
        risk_percentage: Decimal,
        entry_price: Decimal,
        stop_loss_price: Decimal,
        take_profit_price: Decimal | None = None,
        base_exchange_rate: Decimal = Decimal("1.0"),
    ) -> RiskPlan:
        """
        Calculate allowed position size based on account risk threshold.

        Formula:
          Risk Amount ($) = Account Balance * (Risk % / 100)
          Stop Loss (pips) = |Entry - StopLoss| / Pip Size
          Pip Value ($ per unit) = Pip Size / Quote-to-USD rate
          Position Size (Units) = Risk Amount / (Stop Loss in price * conversion)
        """
        if account_balance <= Decimal("0"):
            raise ValidationError("Account balance must be greater than zero.")
        if risk_percentage <= Decimal("0") or risk_percentage > Decimal("100"):
            raise ValidationError("Risk percentage must be between 0.1% and 100%.")
        if entry_price <= Decimal("0") or stop_loss_price <= Decimal("0"):
            raise ValidationError("Entry and Stop Loss prices must be positive numbers.")
        if entry_price == stop_loss_price:
            raise ValidationError("Entry price and Stop Loss price cannot be equal.")

        pip_size = cls.get_pip_size(pair)
        stop_loss_diff = abs(entry_price - stop_loss_price)
        stop_loss_pips = (stop_loss_diff / pip_size).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        risk_amount = (account_balance * (risk_percentage / Decimal("100"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        normalized = pair.upper().replace("/", "").replace("_", "")
        if normalized.endswith("USD"):
            pip_value_per_standard_lot = Decimal("10.00")
        elif normalized.endswith("JPY"):
            pip_value_per_standard_lot = ((Decimal("0.01") / entry_price) * Decimal("100000")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            pip_value_per_standard_lot = (Decimal("10.00") * base_exchange_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        risk_per_standard_lot = stop_loss_pips * pip_value_per_standard_lot
        if risk_per_standard_lot <= Decimal("0"):
            raise ValidationError("Calculated risk per lot resulted in zero.")

        standard_lots = (risk_amount / risk_per_standard_lot).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        mini_lots = (standard_lots * Decimal("10")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        micro_lots = (standard_lots * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        units = int(standard_lots * Decimal("100000"))

        take_profit_pips: Decimal | None = None
        risk_reward_ratio: Decimal | None = None

        if take_profit_price is not None and take_profit_price > Decimal("0"):
            tp_diff = abs(take_profit_price - entry_price)
            take_profit_pips = (tp_diff / pip_size).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if stop_loss_diff > Decimal("0"):
                risk_reward_ratio = (tp_diff / stop_loss_diff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return RiskPlan(
            pair=pair,
            account_balance=account_balance,
            risk_percentage=risk_percentage,
            risk_amount=risk_amount,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips,
            risk_reward_ratio=risk_reward_ratio,
            pip_value_per_standard_lot=pip_value_per_standard_lot,
            units=units,
            standard_lots=standard_lots,
            mini_lots=mini_lots,
            micro_lots=micro_lots,
        )
