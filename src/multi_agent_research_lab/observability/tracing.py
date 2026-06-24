"""Tracing hooks.

This file intentionally avoids binding to one provider. A minimal in-memory sink is used
by default; LangSmith/Langfuse/OpenTelemetry providers can be plugged in by emitting spans
to those backends instead of (or in addition to) the local sink.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter, time
from typing import Any

# Minimal in-process span sink so callers (e.g. the workflow) can export collected spans.
spans: list[dict[str, Any]] = []


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context: records name/attributes/timing and appends to the local sink."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "start_ts": time(),
        "duration_seconds": None,
    }
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        spans.append(span)
