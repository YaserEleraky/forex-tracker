import argparse
import sys
from core.config import Config
from core.exceptions import ForexError
from core.logger import logger
from services.forex_service import ForexService


def cmd_version(args) -> None:
    """عرض معلومات الإصدار الحالية.
    check the configuration file for app_name and version, and print them. If not found, use default values.
    args: The command-line arguments passed to the version command (not used in this function).
    """
    config = Config()
    app_name = config.get("app_name", "Forex Tracker")
    version = config.get("version", "0.1.0")
    print(f"{app_name} v{version}")


def cmd_status(args) -> None:
    """فحص حالة النظام والإعدادات الأساسية.
    check the configuration file for app_name, log_file, and data_dir, and print them. If not found, use default values.
    args: The command-line arguments passed to the status command (not used in this function).
    """
    config = Config()
    print("--- Forex Tracker Status ---")
    print(f"App: {config.get('app_name')}")
    print(f"Log File: {config.get('log_file')}")
    print(f"Data Dir: {config.get('data_dir')}")
    logger.info("CLI status command executed successfully.")


def cmd_price(args: argparse.Namespace) -> None:
    """جلب وعرض السعر اللحظي الحالي لزوج العملات."""
    pair = getattr(args, "pair", "EUR/USD").upper()
    service = ForexService()

    try:
        price = service.get_current_price(pair=pair)
        print(f"\n💵 {pair} Current Price: {price}\n")
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر price: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


def cmd_fetch(args: argparse.Namespace) -> None:
    """جلب أحدث الشموع من الـ API وحفظها في قاعدة البيانات."""
    pair = getattr(args, "pair", "EUR/USD").upper()
    limit = getattr(args, "limit", 1)
    service = ForexService()

    try:
        candles = service.fetch_and_store(pair=pair, limit=limit)
        print(f"\n Successfully fetched and saved {len(candles)} candle(s) for {pair}:")
        for c in candles:
            print(
                f"  • {c.timestamp} | Close: {c.close} | High: {c.high} | Low: {c.low}"
            )
        print()
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر fetch: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    """عرض الشموع المحفوظة محلياً في جدول منسق."""
    pair = getattr(args, "pair", "EUR/USD").upper()
    limit = getattr(args, "limit", 10)
    service = ForexService()

    try:
        candles = service.get_history(pair=pair, limit=limit)
        if not candles:
            print(f"\nNo saved candles found for {pair}. Run 'forex fetch' first.\n")
            return

        print(f"\n--- Stored Candles for {pair} (Last {len(candles)}) ---")
        header = f"{'Date / Time':<20} | {'Open':<10} | {'High':<10} | {'Low':<10} | {'Close':<10} | {'Volume':<8}"
        print(header)
        print("-" * len(header))

        for c in candles:
            ts_str = c.timestamp.strftime("%Y-%m-%d %H:%M")
            print(
                f"{ts_str:<20} | {str(c.open):<10} | {str(c.high):<10} | {str(c.low):<10} | {str(c.close):<10} | {c.volume:<8}"
            )
        print()
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر list: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
