"""
services/risk_service.py
Service layer coordinating risk management calculations.
"""
from __future__ import annotations
from decimal import Decimal

from core.logger import logger
from core.pair import CurrencyPair
from core.risk import RiskCalculator, RiskPlan
from services.forex_service import ForexService


class RiskService:
    """Coordinates risk calculations with optional market price lookups."""

    def __init__(self, forex_service: ForexService | None = None) -> None:
        self.forex_service = forex_service or ForexService()

    def calculate_plan(
        self,
        pair: str,
        account_balance: Decimal,
        risk_pct: Decimal,
        entry: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        sl_pips: Decimal | None = None,
        tp_pips: Decimal | None = None,
    ) -> RiskPlan:
        """
        Construct a risk assessment plan. If entry is omitted, fetches the current price.
        If SL or TP prices are omitted but pips are provided, derives exact price targets.
        """
        validated_pair = CurrencyPair.from_string(pair)
        symbol = validated_pair.symbol
        pip_size = RiskCalculator.get_pip_size(symbol)

        if entry is None or entry <= Decimal("0"):
            entry = self.forex_service.get_current_price(symbol)
            logger.info(f"Using live market price as entry for {symbol}: {entry}")

        if stop_loss is None or stop_loss <= Decimal("0"):
            if sl_pips is None or sl_pips <= Decimal("0"):
                sl_pips = Decimal("30.0")
            stop_loss = entry - (sl_pips * pip_size)

        if (take_profit is None or take_profit <= Decimal("0")) and tp_pips is not None and tp_pips > Decimal("0"):
            take_profit = entry + (tp_pips * pip_size)

        plan = RiskCalculator.compute_position_size(
            pair=symbol,
            account_balance=account_balance,
            risk_percentage=risk_pct,
            entry_price=entry,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
        )

        logger.info(
            f"Risk plan calculated for {symbol}: Risk=${plan.risk_amount} "
            f"Lots={plan.standard_lots} SL={plan.stop_loss_pips} pips"
        )
        return plan
