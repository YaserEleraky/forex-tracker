import argparse
import sys
from core.config import Config
from cli.commands import (
    cmd_version,
    cmd_status,
    cmd_price,
    cmd_fetch,
    cmd_list,
    cmd_watchlist,
    cmd_analyze,
    cmd_alert_add,
    cmd_alert_list,
    cmd_alert_check,
    cmd_alert_delete,
    cmd_cache_clear,
    cmd_backtest,  # <-- أضف هذا
)


def build_parser() -> argparse.ArgumentParser:
    """
    thsis function builds the argument parser for the CLI tool. It defines the available commands and their associated functions. The parser is configured to display help messages and handle command-line arguments.
    Returns:
        argparse.ArgumentParser: The configured argument parser.
    use the Config class to get the app_name from the configuration file. If not found, use a default value.
    case the user runs the CLI tool without any arguments, the parser will display the help message and exit gracefully.
    """
    config = Config()
    app_name = config.get("app_name", "Forex Tracker")

    parser = argparse.ArgumentParser(
        prog="forex", description=f"{app_name} CLI Analysis Tool"
    )
    subparsers = parser.add_subparsers(
        dest="command", title="Commands", description="Available Cli Action"
    )

    # Version command
    p_version = subparsers.add_parser(
        "version", help="Show current application version"
    )
    p_version.set_defaults(func=cmd_version)

    # Status command
    p_status = subparsers.add_parser(
        "status", help="Check system status and basic settings"
    )
    p_status.set_defaults(func=cmd_status)

    # 3. أمر price
    p_price = subparsers.add_parser("price", help="Get real-time exchange rate")
    p_price.add_argument(
        "--pair",
        type=str,
        default="EUR/USD",
        help="Currency pair (e.g., EUR/USD, USD/JPY)",
    )
    p_price.set_defaults(func=cmd_price)

    # 4. أمر fetch
    p_fetch = subparsers.add_parser(
        "fetch", help="Fetch candles from API and store in SQLite"
    )
    p_fetch.add_argument(
        "--pairs",
        type=str,
        default="EUR/USD",
        help="Currency pair or comma-separated pairs (e.g., EUR/USD,GBP/USD,USD/JPY)",
    )
    p_fetch.add_argument(
        "--interval",
        type=str,
        default="1day",
        help="Timeframe interval (e.g., 1min, 5min, 1h, 4h, 1day)",
    )
    p_fetch.add_argument(
        "--limit", type=int, default=1, help="Number of candles to fetch (default: 1)"
    )
    p_fetch.set_defaults(func=cmd_fetch)

    # 5. أمر list
    p_list = subparsers.add_parser("list", help="List stored candles from database")
    p_list.add_argument(
        "--pair", type=str, default="EUR/USD", help="Currency pair (default: EUR/USD)"
    )
    p_list.add_argument(
        "--interval",
        type=str,
        default="1day",
        help="Timeframe interval (default: 1day)",
    )
    p_list.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of candles to display (default: 10)",
    )
    p_list.set_defaults(func=cmd_list)

    # 6. أمر watchlist
    p_watch = subparsers.add_parser(
        "watchlist", help="Monitor a list of currency pairs live"
    )
    p_watch.add_argument(
        "--pairs",
        type=str,
        default="EUR/USD,GBP/USD,USD/JPY",
        help="Comma-separated pairs list (default: EUR/USD,GBP/USD,USD/JPY)",
    )
    p_watch.set_defaults(func=cmd_watchlist)

    # 7. أمر analyze
    p_analyze = subparsers.add_parser(
        "analyze", help="Run technical indicators and analyze pair"
    )
    p_analyze.add_argument(
        "--pair", type=str, default="EUR/USD", help="Currency pair (default: EUR/USD)"
    )
    p_analyze.add_argument(
        "--interval",
        type=str,
        default="1day",
        help="Timeframe interval (default: 1day)",
    )
    p_analyze.add_argument(
        "--limit",
        type=int,
        default=35,
        help="Number of candles to analyze (default: 35)",
    )
    p_analyze.add_argument(
        "--indicators",
        type=str,
        default="sma,rsi,macd",
        help="Comma-separated indicators: sma,ema,rsi,macd (default: sma,rsi,macd)",
    )
    p_analyze.set_defaults(func=cmd_analyze)

    # 8. أمر alert والعمليات التابعة له
    p_alert = subparsers.add_parser("alert", help="Manage price and indicator triggers")
    alert_sub = p_alert.add_subparsers(
        dest="alert_command",
        title="Alert Operations",
        description="Available alert actions",
    )

    # alert add
    p_add = alert_sub.add_parser("add", help="Add a new alert condition")
    p_add.add_argument(
        "--pair", type=str, required=True, help="Currency pair (e.g., EUR/USD)"
    )
    p_add.add_argument(
        "--condition",
        type=str,
        required=True,
        help="Condition (e.g., 'price > 1.0900', 'rsi < 30')",
    )
    p_add.add_argument(
        "--interval",
        type=str,
        default="1day",
        help="Timeframe interval (default: 1day)",
    )
    p_add.add_argument("--message", type=str, default="", help="Custom alert message")
    p_add.set_defaults(func=cmd_alert_add)

    # alert list
    p_alist = alert_sub.add_parser("list", help="List registered alerts")
    p_alist.add_argument(
        "--active", action="store_true", help="List only active alerts"
    )
    p_alist.set_defaults(func=cmd_alert_list)

    # alert check
    p_check = alert_sub.add_parser(
        "check", help="Evaluate active alerts against current market data"
    )
    p_check.add_argument(
        "--pair", type=str, default=None, help="Filter check to a specific pair"
    )
    p_check.set_defaults(func=cmd_alert_check)

    # alert delete
    p_del = alert_sub.add_parser("delete", help="Delete an alert by ID")
    p_del.add_argument("--id", type=str, required=True, help="Alert ID to delete")
    p_del.set_defaults(func=cmd_alert_delete)

    # 9. أمر cache
    p_cache = subparsers.add_parser("cache", help="Manage application cache layer")
    cache_sub = p_cache.add_subparsers(
        dest="cache_command",
        title="Cache Operations",
        description="Available cache operations",
    )

    p_cache_clear = cache_sub.add_parser("clear", help="Clear all cached market data")
    p_cache_clear.set_defaults(func=cmd_cache_clear)

    # 10. أمر backtest
    p_backtest = subparsers.add_parser(
        "backtest", help="Simulate and test trading strategies on historical data"
    )
    p_backtest.add_argument(
        "--pair", type=str, default="EUR/USD", help="Currency pair (default: EUR/USD)"
    )
    p_backtest.add_argument(
        "--interval",
        type=str,
        default="1day",
        help="Timeframe interval (default: 1day)",
    )
    p_backtest.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of historical candles (default: 100)",
    )
    p_backtest.add_argument(
        "--fast", type=int, default=10, help="Fast SMA period (default: 10)"
    )
    p_backtest.add_argument(
        "--slow", type=int, default=30, help="Slow SMA period (default: 30)"
    )
    p_backtest.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial account capital (default: 10000)",
    )
    p_backtest.add_argument(
        "--size",
        type=float,
        default=10000.0,
        help="Trade position size (default: 10000)",
    )
    p_backtest.set_defaults(func=cmd_backtest)
    return parser


def main() -> None:
    """نقطة الدخول الرئيسية للأداة (Entry point).
    this function serves as the main entry point for the CLI tool. It builds the argument parser, processes command-line arguments, and executes the corresponding command functions based on user input.
    """
    parser = build_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
