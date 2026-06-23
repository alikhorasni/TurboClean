from __future__ import annotations

import functools
import logging
import time
import tracemalloc
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("puredata.benchmark")

def benchmark(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that logs execution time and peak memory usage."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracemalloc.start()
        t0 = time.monotonic()
        try:
            result = func(*args, **kwargs)
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.monotonic() - t0
            logger.info(
                f"{func.__name__}: {elapsed:.4f}s, "
                f"peak memory {peak / 1024**2:.2f} MiB"
            )
        return result
    return wrapper
