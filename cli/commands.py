import argparse
import sys
from core.config import Config
from core.exceptions import ForexError
from core.logger import logger
from services.forex_service import ForexService


def cmd_version(args: argparse.Namespace) -> None:
    """عرض إصدار التطبيق."""
    config = Config()
    app_name = config.get("app_name", "Forex Tracker")
    version = config.get("version", "0.1.0")
    print(f"{app_name} v{version}")


def cmd_status(args: argparse.Namespace) -> None:
    """فحص حالة النظام ومسارات البيانات."""
    config = Config()
    print("--- Forex Tracker Status ---")
    print(f"App Name : {config.get('app_name', 'Forex Tracker')}")
    print(f"Version  : {config.get('version', '0.1.0')}")
    print(f"Data Dir : {config.get('data_dir', './data')}")
    print(f"Log File : {config.get('log_file', './logs/app.log')}")
    print("Status   : Ready")


def cmd_price(args: argparse.Namespace) -> None:
    """جلب وعرض السعر اللحظي الحالي لزوج العملات."""
    pair = getattr(args, "pair", "EUR/USD")
    service = ForexService()

    try:
        price = service.get_current_price(pair=pair)
        print(f"\n💵 {pair.upper()} Current Price: {price}\n")
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر price: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


def cmd_fetch(args: argparse.Namespace) -> None:
    """جلب الشموع لزوج واحد أو عدة أزواج وتخزينها في قاعدة البيانات."""
    raw_pairs = getattr(args, "pairs", None) or getattr(args, "pair", "EUR/USD")
    pairs_list = [p.strip() for p in raw_pairs.split(",") if p.strip()]
    interval = getattr(args, "interval", "1day")
    limit = getattr(args, "limit", 1)

    service = ForexService(rate_limit_delay=1.0)

    try:
        if len(pairs_list) == 1:
            pair = pairs_list[0]
            candles = service.fetch_and_store(pair=pair, interval=interval, limit=limit)
            print(
                f"\n✅ Successfully fetched and stored {len(candles)} candle(s) for {pair.upper()} [{interval}]:"
            )
            for c in candles:
                print(
                    f"  • {c.timestamp} | Close: {c.close} | High: {c.high} | Low: {c.low}"
                )
            print()
        else:
            print(
                f"\n⏳ Fetching batch data for {len(pairs_list)} pairs [{interval}]..."
            )
            results = service.fetch_and_store_multiple(
                pairs=pairs_list, interval=interval, limit=limit
            )
            print("\n--- Batch Ingestion Results ---")
            for pair, candles in results.items():
                status = f"✅ {len(candles)} candles" if candles else "❌ Failed"
                print(f"  • {pair.upper():<10} : {status}")
            print()
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر fetch: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    """عرض الشموع المحفوظة محلياً لزوج وإطار زمني محددين."""
    pair = getattr(args, "pair", "EUR/USD")
    interval = getattr(args, "interval", "1day")
    limit = getattr(args, "limit", 10)
    service = ForexService()

    try:
        candles = service.get_history(pair=pair, interval=interval, limit=limit)
        if not candles:
            print(
                f"\nNo stored candles found for {pair.upper()} with interval '{interval}'. Run 'forex fetch' first.\n"
            )
            return

        print(
            f"\n--- Stored Candles: {pair.upper()} [{interval}] (Last {len(candles)}) ---"
        )
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


def cmd_watchlist(args: argparse.Namespace) -> None:
    """عرض مقارنة حية لأسعار قائمة المراقبة."""
    raw_pairs = getattr(args, "pairs", "EUR/USD,GBP/USD,USD/JPY")
    pairs_list = [p.strip() for p in raw_pairs.split(",") if p.strip()]

    service = ForexService(rate_limit_delay=1.0)

    try:
        print(f"\n⏳ Loading live quotes for: {', '.join(pairs_list)}...")
        summary = service.get_watchlist(pairs=pairs_list)

        if not summary:
            print(
                "Failed to retrieve watchlist data. Check your API key or connection."
            )
            return

        print("\n--- Live Forex Watchlist ---")
        header = f"{'Pair':<10} | {'Current / Close':<15} | {'High':<12} | {'Low':<12} | {'Time (UTC)':<16}"
        print(header)
        print("-" * len(header))

        for item in summary:
            time_str = item["time"].strftime("%Y-%m-%d %H:%M")
            print(
                f"{item['pair']:<10} | {str(item['close']):<15} | {str(item['high']):<12} | {str(item['low']):<12} | {time_str:<16}"
            )
        print()
    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر watchlist: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
