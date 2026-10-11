import json
from pathlib import Path
from typing import Any, Optional
from core.exceptions import ConfigError


class Config:
    """
    Singleton class to manage application configuration
    """

    _instance: Optional["Config"] = None
    _data: dict[str, Any] = {}
    _config_file: Path = Path(__file__).resolve().parent.parent / "config.json"

    def __new__(cls) -> "Config":
        """
        Create a new instance of Config if it doesn't exist, otherwise return the existing instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """
        Load configuration data from the JSON file. Raises ConfigError if the file is not found or cannot be parsed.
        """
        if not self._config_file.exists():
            raise ConfigError(f"Configuration file not found: {self._config_file}")

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value by key. Returns the default value if the key is not found.
        """
        return self._data.get(key, default)

    def reload(self) -> None:
        """
        Reload the configuration data from the JSON file. This allows for dynamic updates to the configuration without restarting the application.
        """
        self._load_config()

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance and clear the configuration data. This is useful for testing purposes.
        """
        cls._instance = None
        cls._data = {}
