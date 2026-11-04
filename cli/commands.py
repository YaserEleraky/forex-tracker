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


def cmd_analyze(args: argparse.Namespace) -> None:
    """تحليل الشموع المخزنة لزوج عملات وعرض مصفوفة المؤشرات الفنية."""
    pair = getattr(args, "pair", "EUR/USD")
    interval = getattr(args, "interval", "1day")
    limit = getattr(args, "limit", 30)
    raw_indicators = getattr(args, "indicators", "sma,rsi,macd")
    indicators_list = [ind.strip() for ind in raw_indicators.split(",") if ind.strip()]

    service = ForexService()

    try:
        report = service.analyze_pair(
            pair=pair,
            interval=interval,
            limit=limit,
            indicators=indicators_list,
        )

        if report["candles_count"] == 0:
            print(f"\n⚠️  No stored candles found for {pair.upper()} [{interval}].")
            print(
                f"👉 Please run: forex fetch --pairs {pair.upper()} --interval {interval} --limit {max(limit, 35)}\n"
            )
            return

        indicators = report["indicators"]
        candles_count = report["candles_count"]

        print(f"\n========================================================")
        print(
            f" 📊 Technical Analysis: {report['pair']} [{report['interval']}] (Evaluated: {candles_count} candles)"
        )
        print(f"========================================================")

        # استخراج آخر القيم لحساب الملخص
        latest_candle = report["latest_candle"]
        print(
            f"• Latest Close : {latest_candle.close} (at {latest_candle.timestamp.strftime('%Y-%m-%d %H:%M')})"
        )

        # 1. تفسير RSI
        if "rsi_14" in indicators and indicators["rsi_14"]:
            last_rsi = indicators["rsi_14"][-1].value
            if last_rsi is not None:
                sentiment = "Neutral"
                if last_rsi >= 70:
                    sentiment = "🔥 Overbought (ذروة شراء - احتمال تصحيح هابط)"
                elif last_rsi <= 30:
                    sentiment = "❄️ Oversold (ذروة بيع - احتمال ارتداد صاعد)"
                print(f"• RSI (14)     : {last_rsi} -> {sentiment}")

        # 2. تفسير MACD
        if "macd" in indicators and indicators["macd"]:
            last_macd_res = indicators["macd"][-1].extra
            if (
                last_macd_res
                and last_macd_res.get("macd") is not None
                and last_macd_res.get("signal") is not None
            ):
                macd_line = last_macd_res["macd"]
                signal_line = last_macd_res["signal"]
                hist = last_macd_res["histogram"]
                bias = (
                    "🟢 Bullish Momentum (زخم صاعد)"
                    if macd_line > signal_line
                    else "🔴 Bearish Momentum (زخم هابط)"
                )
                print(
                    f"• MACD (12,26) : {macd_line} | Signal (9): {signal_line} | Hist: {hist} -> {bias}"
                )

        # 3. تفسير SMA
        if "sma_20" in indicators and indicators["sma_20"]:
            last_sma = indicators["sma_20"][-1].value
            if last_sma is not None:
                trend = (
                    "Above SMA (اتجاه صاعد قصير المدى)"
                    if latest_candle.close >= last_sma
                    else "Below SMA (اتجاه هابط قصير المدى)"
                )
                print(f"• SMA (20)     : {last_sma} -> {trend}")

        print("\n--- Recent Candles Matrix (Last 5) ---")
        row_fmt = "{:<17} | {:<10} | {:<10} | {:<10} | {:<18}"
        print(row_fmt.format("Timestamp", "Close", "SMA(20)", "RSI(14)", "MACD (Hist)"))
        print("-" * 75)

        # عرض آخر 5 شموع متزامنة مع المؤشرات
        start_idx = max(0, candles_count - 5)
        for i in range(start_idx, candles_count):
            sma_val = indicators.get("sma_20", [None] * candles_count)[i]
            rsi_val = indicators.get("rsi_14", [None] * candles_count)[i]
            macd_val = indicators.get("macd", [None] * candles_count)[i]

            s_str = (
                str(sma_val.value) if (sma_val and sma_val.value is not None) else "N/A"
            )
            r_str = (
                str(rsi_val.value) if (rsi_val and rsi_val.value is not None) else "N/A"
            )
            m_str = (
                str(macd_val.extra.get("histogram"))
                if (
                    macd_val
                    and macd_val.extra
                    and macd_val.extra.get("histogram") is not None
                )
                else "N/A"
            )

            # استرجاع توقيت وسعر الإغلاق من أحد المؤشرات أو الشمعة
            ts_str = sma_val.timestamp.strftime("%Y-%m-%d %H:%M") if sma_val else "N/A"

            # نحصل على سعر الإغلاق للشمعة
            history_candles = service.get_history(
                pair=pair, interval=interval, limit=candles_count
            )
            sorted_history = sorted(history_candles, key=lambda c: c.timestamp)
            c_close = str(sorted_history[i].close) if i < len(sorted_history) else "N/A"

            print(row_fmt.format(ts_str, c_close, s_str, r_str, m_str))
        print()

    except ForexError as err:
        logger.error(f"فشل تنفيذ أمر analyze: {err}")
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)
