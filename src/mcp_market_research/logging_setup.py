from __future__ import annotations

import logging
import sys
import time
from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import structlog

from .config import Settings

_request_id: ContextVar[str | None] = ContextVar("_request_id", default=None)


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()


def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)
    structlog.contextvars.bind_contextvars(request_id=request_id)


def clear_request_id() -> None:
    _request_id.set(None)
    structlog.contextvars.unbind_contextvars("request_id")


P = ParamSpec("P")
R = TypeVar("R")


def traced_tool(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that logs entry/exit and duration for an MCP tool function."""

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        log = get_logger("mcp.tool")

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            log.debug("tool_start", tool=name)
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                log.error(
                    "tool_error",
                    tool=name,
                    duration_ms=duration_ms,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
                raise
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info("tool_ok", tool=name, duration_ms=duration_ms)
            return result

        return wrapper

    return decorator


def log_extra(**fields: Any) -> None:
    structlog.contextvars.bind_contextvars(**fields)
