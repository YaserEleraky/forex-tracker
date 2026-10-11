from __future__ import annotations
import functools
import time
from typing import Callable, Any
from core.logger import logger


def timer(fun: Callable) -> Callable:
    """
    This decorator measures the execution time of the decorated function and logs it using the application's logger.
    It can be applied to any function to automatically log how long it takes to execute.
    use the logger from core.logger to log the execution time of the decorated function.
    Using functools.wraps to preserve the original function's metadata (like name and docstring) when it is decorated.
    returns: A wrapper function that logs the execution time of the original function.
    args: The function to be decorated.
    """

    @functools.wraps(fun)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = fun(*args, **kwargs)
        end = time.time()
        logger.info(f"{fun.__name__} took {end - start:.4f} seconds to execute.")
        return result

    return wrapper
