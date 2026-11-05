from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.candle import Candle
from core.exceptions import ValidationError
from core.intervals import Interval
from core.logger import logger
from core.pair import CurrencyPair
from core.strategy import BaseStrategy
from core.trade import SignalType, Trade, TradeStatus
from storage.base import Storage
from storage.sqlite_storage import SQLiteStorage


@dataclass
class BacktestResult:
    """كائن يحمل المخرجات الإحصائية والمالية لعملية الاختبار التاريخي."""

    pair: str
    interval: str
    strategy_name: str
    initial_capital: Decimal
    final_capital: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: Decimal
    roi_percent: float
    max_drawdown_percent: float
    profit_factor: float
    trades: list[Trade] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "interval": self.interval,
            "strategy": self.strategy_name,
            "initial_capital": float(self.initial_capital),
            "final_capital": float(self.final_capital),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate, 2),
            "total_pnl": float(self.total_pnl),
            "roi_percent": round(self.roi_percent, 2),
            "max_drawdown_percent": round(self.max_drawdown_percent, 2),
            "profit_factor": round(self.profit_factor, 2),
        }


class BacktestService:
    """منسق ومحاكي التداول التاريخي."""

    def __init__(self, storage: Storage | None = None) -> None:
        self.storage = storage or SQLiteStorage()

    def run(
        self,
        strategy: BaseStrategy,
        pair: str,
        interval: str = "1day",
        limit: int = 100,
        initial_capital: Decimal = Decimal("10000.0"),
        trade_size: Decimal = Decimal("10000.0"),
    ) -> BacktestResult:
        """
        تشغيل محاكاة الاستراتيجية على الشموع التاريخية المخزنة.
        """
        validated_pair = CurrencyPair.from_string(pair)
        validated_interval = Interval.from_str(interval)

        candles = self.storage.get_candles(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            limit=limit,
        )

        if not candles:
            raise ValidationError(
                f"لا توجد شموع مخزنة لزوج {validated_pair.symbol} على إطار {validated_interval.value}. "
                f"استخدم أمر 'forex fetch' أولاً لجلب البيانات."
            )

        # ترتيب الشموع زمنياً من الأقدم إلى الأحدث
        candles_sorted = sorted(candles, key=lambda c: c.timestamp)

        capital = initial_capital
        peak_capital = initial_capital
        max_drawdown = Decimal("0.0")

        open_trade: Trade | None = None
        executed_trades: list[Trade] = []

        for i, candle in enumerate(candles_sorted):
            signal = strategy.generate_signal(i, candles_sorted)

            # 1. إشارة شراء ولم تكن هناك صفقة مفتوحة
            if signal == SignalType.BUY and open_trade is None:
                open_trade = Trade(
                    pair=validated_pair.symbol,
                    entry_time=candle.timestamp,
                    entry_price=candle.close,
                    size=trade_size,
                )

            # 2. إشارة بيع مع وجود صفقة شراء مفتوحة -> إغلاق الصفقة
            elif signal == SignalType.SELL and open_trade is not None:
                open_trade.close(exit_time=candle.timestamp, exit_price=candle.close)
                capital += open_trade.pnl
                executed_trades.append(open_trade)
                open_trade = None

            # تحديث أقصى هبوط تاريخي (Max Drawdown)
            if capital > peak_capital:
                peak_capital = capital
            drawdown = (peak_capital - capital) / peak_capital * Decimal("100")
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 3. إغلاق أي صفقة معلقة عند نهاية المحاكاة بسعر آخر شمعة
        if open_trade is not None:
            last_candle = candles_sorted[-1]
            open_trade.close(
                exit_time=last_candle.timestamp, exit_price=last_candle.close
            )
            capital += open_trade.pnl
            executed_trades.append(open_trade)

        # 4. تجميع الإحصائيات المالية
        total_trades = len(executed_trades)
        winning_trades = sum(1 for t in executed_trades if t.pnl > Decimal("0.0"))
        losing_trades = sum(1 for t in executed_trades if t.pnl < Decimal("0.0"))

        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        total_pnl = capital - initial_capital
        roi_percent = float((total_pnl / initial_capital) * Decimal("100"))

        gross_profit = sum(
            (t.pnl for t in executed_trades if t.pnl > 0), Decimal("0.0")
        )
        gross_loss = abs(
            sum((t.pnl for t in executed_trades if t.pnl < 0), Decimal("0.0"))
        )
        profit_factor = (
            float(gross_profit / gross_loss)
            if gross_loss > 0
            else (float(gross_profit) if gross_profit > 0 else 1.0)
        )

        logger.info(
            f"Backtest completed for {validated_pair.symbol} [{strategy.name}]: "
            f"Trades={total_trades}, WinRate={win_rate:.1f}%, ROI={roi_percent:.2f}%"
        )

        return BacktestResult(
            pair=validated_pair.symbol,
            interval=validated_interval.value,
            strategy_name=strategy.name,
            initial_capital=initial_capital,
            final_capital=capital,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            roi_percent=roi_percent,
            max_drawdown_percent=float(max_drawdown),
            profit_factor=profit_factor,
            trades=executed_trades,
        )
