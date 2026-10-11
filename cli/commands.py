"""
cli/commands.py
منطق تنفيذ الأوامر الخاصة بالـ CLI.
"""

from core.config import Config
from core.logger import logger


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
