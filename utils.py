import time
from loguru import logger

def time_track(callback):
    start_time = time.time()
    result = callback()
    end_time = time.time()
    logger.info(f"took {end_time-start_time} seconds")
    return result
