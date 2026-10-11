from __future__ import annotations
import logging
from pathlib import Path
from core.config import Config


def setup_logger(name: str = "forex_tracker") -> logging.Logger:
    """
    Set up a logger with file and console handlers and a specific format. The log file path is retrieved from the configuration file.
    use the Config class to get the log file path from the configuration file. If the log file path is not specified in the configuration, it defaults to './logs/app.log'.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """
    Logger = logging.getLogger(name)

    if Logger.hasHandlers():
        return Logger

    Logger.setLevel(logging.INFO)

    config = Config()
    log_file_path = config.get("log_file", "./logs/app.log")
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setFormatter(formatter)
    Logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    Logger.addHandler(console_handler)

    return Logger


logger = setup_logger()
