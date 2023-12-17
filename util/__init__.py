import time
import random
import functools
from loguru import logger


def time_track(func=None,description:str=""):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            start_time = time.time()
            result = func(*args,**kwargs)
            end_time = time.time()
            time_diff = round(end_time - start_time,2)
            log = logger.success
            if time_diff > 0.75:
                log = logger.warning
            log(f"{description} took {time_diff} seconds")
            return result
        return inner
    if func is not None:
        return decorator(func)
        
    return decorator

def add_noise(value, noise_factor=0.0000000099):
    noise = random.uniform(0, noise_factor)
    noisy_value = value + noise
    return noisy_value

def is_equal_float(a:float,b:float,precision=6):
    difference = abs(a - b)
    threshold = 10 ** -precision
    return difference < threshold



__all__ = ["time_track","add_noise","is_equal_float"]
