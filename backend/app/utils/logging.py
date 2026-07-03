"""
Structured logging configuration using structlog.

Why structlog over stdlib logging?
- Structured key-value pairs (not free-form strings) → machine-parseable
- Context variables (request_id, user_id) automatically added to every log line
- JSON output in production → compatible with ELK, Datadog, CloudWatch
- Pretty console output in development → human-readable
- Performance: structlog is faster than stdlib logging with formatters

Why not loguru?
- Loguru is great for simple apps but doesn't integrate as cleanly with
  asyncio context variables (for request ID propagation)
- structlog's contextvars integration is purpose-built for async frameworks

Usage:
    import structlog
    logger = structlog.get_logger(__name__)

    logger.info("document_processed", document_id=doc_id, chunks=42, duration_ms=1200)
    # Dev output: [info] document_processed  document_id=abc123 chunks=42 duration_ms=1200
    # Prod output: {"event": "document_processed", "document_id": "abc123", "chunks": 42, ...}
"""

import logging
import sys

import structlog


def setup_logging(log_level: str = "DEBUG", log_format: str = "console") -> None:
    """
    Configure structlog for the application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "console" for dev, "json" for production.
    """
    # Shared processors for both dev and prod
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # Production: JSON output for log aggregation systems
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: colorful, human-readable console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog's formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

    # Quiet down noisy third-party loggers
    for noisy_logger in ["uvicorn.access", "httpx", "httpcore", "sqlalchemy.engine"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
