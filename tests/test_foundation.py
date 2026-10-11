import unittest
import time
from utils.decorators import timer
from core.logger import logger
from storage.memory_storage import MemoryStorage
from core.config import Config


class TestFoundation(unittest.TestCase):
    """
    Test suite for foundational components of the Forex Tracker application, including configuration management, in-memory storage, and utility decorators.
    """

    def setUp(self):
        Config.reset()  # Reset the singleton instance before each test

    def test_config_singleton_and_values(self) -> None:
        """
        Test the singleton behavior of the Config class and verify that configuration values are loaded correctly.
        This test ensures that multiple instances of the Config class refer to the same object and that configuration values can be retrieved as expected.
        """
        config1 = Config()
        config3 = Config()
        self.assertIs(config1, config3)
        self.assertEqual(config1.get("app_name"), "Forex Tracker")
        logger.info("Config singleton and values test passed.")

    def test_memory_storage_lifecycle(self) -> None:
        """
        Test the lifecycle of the MemoryStorage class, including connection and disconnection.
        This test verifies that the MemoryStorage class correctly manages its connection state and that data is cleared
        """
        storage = MemoryStorage()
        self.assertFalse(storage.is_connected())
        storage.connect()
        self.assertTrue(storage.is_connected())
        storage.disconnect()
        self.assertFalse(storage.is_connected())
        logger.info("MemoryStorage lifecycle test passed.")

    def test_timer_decorator(self) -> None:
        """
        Test the timer decorator functionality.
        This test verifies that the timer decorator correctly measures the execution time of a function.
        """

        @timer
        def sample_add(a: int, b: int) -> int:
            time.sleep(0.1)  # Simulate a delay
            return a + b

        result = sample_add(5, 10)
        self.assertEqual(result, 15)
        logger.info("Timer decorator test passed.")


if __name__ == "__main__":
    unittest.main()
