"""Tracing hooks.

A minimal in-memory sink is always recorded. When `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` are configured, spans are mirrored to Langfuse as real
observability data; otherwise Langfuse is skipped entirely (no-op).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter, time
from typing import Any

from multi_agent_research_lab.core.config import Settings, get_settings

# Minimal in-process span sink so callers (e.g. the workflow) can export collected spans.
spans: list[dict[str, Any]] = []

_langfuse_clients: dict[tuple[str | None, str | None, str], Any | None] = {}


def _get_langfuse_client(settings: Settings) -> Any | None:
    """Return a Langfuse client cached by credentials, or None if not configured.

    Caching by credentials (rather than a single global flag) keeps behavior correct when
    callers pass different `Settings` in the same process, e.g. real CLI runs vs. tests that
    force mock credentials.
    """

    key = (settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host)
    if key in _langfuse_clients:
        return _langfuse_clients[key]

    client = None
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    _langfuse_clients[key] = client
    return client


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> Iterator[dict[str, Any]]:
    """Span context: records name/attributes/timing locally, mirrors to Langfuse if configured."""

    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "start_ts": time(),
        "duration_seconds": None,
    }
    client = _get_langfuse_client(settings or get_settings())

    if client is None:
        try:
            yield span
        finally:
            span["duration_seconds"] = perf_counter() - started
            spans.append(span)
        return

    with client.start_as_current_observation(name=name, input=attributes or {}) as langfuse_span:
        try:
            yield span
        finally:
            span["duration_seconds"] = perf_counter() - started
            spans.append(span)
            langfuse_span.update(output={"duration_seconds": span["duration_seconds"]})


def flush_tracing() -> None:
    """Flush any buffered Langfuse events. Call once at the end of a CLI run."""

    for client in _langfuse_clients.values():
        if client is not None:
            client.flush()
