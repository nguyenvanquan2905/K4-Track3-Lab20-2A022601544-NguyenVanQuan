"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, quality proxy, citations, failures, and estimated cost."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    answer = state.final_answer or ""
    claim_lines = [line for line in answer.splitlines() if line.lstrip().startswith("-")]
    cited_claims = sum(bool(re.search(r"\[\d+\]", line)) for line in claim_lines)
    coverage = cited_claims / len(claim_lines) if claim_lines else 0.0
    quality = min(
        10.0,
        (2.0 if answer else 0.0)
        + min(3.0, len(answer) / 500)
        + 3.0 * coverage
        + (2.0 if state.analysis_notes else 0.0),
    )
    recorded_costs = [
        event["payload"].get("cost_usd")
        for event in state.trace
        if event.get("name") == "usage" and isinstance(event.get("payload"), dict)
    ]
    known_costs = [float(cost) for cost in recorded_costs if cost is not None]
    estimated_cost = sum(known_costs) if known_costs else (None if recorded_costs else 0.0)
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality,
        citation_coverage=coverage,
        failure_rate=1.0 if state.errors or not answer else 0.0,
        notes="single-query quality proxy; replace with peer-review score",
    )
    return state, metrics
