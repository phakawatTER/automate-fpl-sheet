import time
import asyncio
import random
import functools
import pytz
from loguru import logger

RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TIMEZONE = pytz.timezone("Asia/Bangkok")


def time_track(func=None, description: str = ""):
    def decorator(func):
        @functools.wraps(func)
        def inner_sync(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            time_diff = round(end_time - start_time, 2)
            log = logger.success
            if time_diff > 0.75:
                log = logger.warning
            log(f"{description} took {time_diff} seconds")
            return result

        async def inner_async(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            time_diff = round(end_time - start_time, 2)
            log = logger.success
            if time_diff > 0.75:
                log = logger.warning
            log(f"{description} took {time_diff} seconds")
            return result

        if asyncio.iscoroutinefunction(func):
            return inner_async
        return inner_sync

    if func is not None:
        return decorator(func)

    return decorator


def add_noise(value, noise_factor=0.0000000099):
    noise = random.uniform(0, noise_factor)
    noisy_value = value + noise
    return noisy_value


def is_equal_float(a: float, b: float, precision=6):
    difference = abs(a - b)
    threshold = 10**-precision
    return difference < threshold


def convert_to_a1_notation(row, col):
    """
    Convert row and column indices to A1 notation.

    Parameters:
        row (int): Row index (1-based).
        col (int): Column index (1-based).

    Returns:
        str: A1 notation representing the cell.
    """
    col_str = ""

    while col > 0:
        col -= 1
        col_str = chr(ord("A") + col % 26) + col_str
        col //= 26

    return f"{col_str}{row}"


__all__ = [
    "time_track",
    "add_noise",
    "is_equal_float",
    "convert_to_a1_notation",
    "RFC3339_FORMAT",
    "TIMEZONE",
]
