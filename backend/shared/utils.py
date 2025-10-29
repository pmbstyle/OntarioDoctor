import time
import logging
from typing import Any, Callable
from functools import wraps
import asyncio


def setup_logging(service_name: str, level: int = logging.INFO):
    """Configure logging for a service"""
    logging.basicConfig(
        level=level,
        format=f'%(asctime)s - {service_name} - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(service_name)


def timeit(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = int((time.time() - start) * 1000)
        logging.debug(f"{func.__name__} took {elapsed}ms")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = int((time.time() - start) * 1000)
        logging.debug(f"{func.__name__} took {elapsed}ms")
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def normalize_text(text: str) -> str:
    """Normalize text for processing"""
    return " ".join(text.strip().split())


def extract_numbers(text: str) -> list[float]:
    """Extract numbers from text"""
    import re
    return [float(n) for n in re.findall(r'\d+\.?\d*', text)]
