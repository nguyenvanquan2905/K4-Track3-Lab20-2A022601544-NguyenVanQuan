"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import Settings, get_settings


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> Iterator[dict[str, Any]]:
    """Capture a provider-neutral span suitable for JSON trace export."""

    runtime_settings = settings or get_settings()
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "provider": "json",
    }
    stack = ExitStack()
    langsmith_run: Any = None
    try:
        if runtime_settings.langsmith_api_key:
            from langsmith import Client, trace, tracing_context

            client = Client(api_key=runtime_settings.langsmith_api_key)
            stack.enter_context(
                tracing_context(
                    enabled=True,
                    project_name=runtime_settings.langsmith_project,
                    client=client,
                )
            )
            langsmith_run = stack.enter_context(
                trace(
                    name,
                    run_type="chain",
                    inputs=attributes or {},
                    project_name=runtime_settings.langsmith_project,
                    client=client,
                )
            )
            span["provider"] = "langsmith"
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started
        if langsmith_run is not None:
            langsmith_run.add_outputs({"duration_seconds": span["duration_seconds"]})
        try:
            stack.close()
        except Exception as exc:
            span["provider_error"] = f"{type(exc).__name__}: {exc}"
