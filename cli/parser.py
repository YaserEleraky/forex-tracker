import argparse
import sys
from cli.commands import (
    cmd_version,
    cmd_status,
    cmd_price,
    cmd_fetch,
    cmd_list,
    cmd_watchlist,
)
from core.config import Config


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
