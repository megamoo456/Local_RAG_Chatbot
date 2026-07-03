"""
Performance timing utilities.

Provides a context manager and decorator for measuring execution time
of any operation. Designed for observability — logs timing data that
can later be exported to LangFuse, Prometheus, or custom dashboards.

Usage as context manager:
    async with Timer("embedding_generation") as t:
        embeddings = await model.encode(chunks)
    print(f"Took {t.elapsed_ms}ms")

Usage as decorator:
    @timed("qdrant_search")
    async def search(query: str):
        ...
"""

import functools
import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class Timer:
    """
    Async-compatible context manager for timing code blocks.

    Records elapsed time in milliseconds and optionally logs it.
    """

    def __init__(self, operation: str, log: bool = True, **extra: Any) -> None:
        """
        Args:
            operation: Name of the operation being timed (for log messages).
            log: Whether to log the timing result automatically.
            **extra: Additional key-value pairs to include in the log.
        """
        self.operation = operation
        self.log = log
        self.extra = extra
        self._start: float = 0
        self.elapsed_ms: float = 0

    async def __aenter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        if self.log:
            logger.info(
                f"timer_{self.operation}",
                operation=self.operation,
                elapsed_ms=round(self.elapsed_ms, 1),
                **self.extra,
            )

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
        if self.log:
            logger.info(
                f"timer_{self.operation}",
                operation=self.operation,
                elapsed_ms=round(self.elapsed_ms, 1),
                **self.extra,
            )


def timed(operation: str):
    """
    Decorator that logs execution time of async or sync functions.

    Args:
        operation: Name of the operation (used in log messages).

    Example:
        @timed("document_parse")
        async def parse_document(file_path: str):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with Timer(operation, log=True):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with Timer(operation, log=True):
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
