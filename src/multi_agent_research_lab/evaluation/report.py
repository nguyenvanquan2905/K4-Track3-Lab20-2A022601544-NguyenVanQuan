"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render metrics and a concise trade-off analysis to Markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citation cov. | Failure rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} "
            f"| {citation} | {failure} | {item.notes} |"
        )
    if len(metrics) >= 2:
        fastest = min(metrics, key=lambda item: item.latency_seconds)
        best = max(metrics, key=lambda item: item.quality_score or 0.0)
        lines.extend(
            [
                "",
                "## Analysis",
                "",
                f"- Fastest run: **{fastest.run_name}** ({fastest.latency_seconds:.2f}s).",
                f"- Highest quality proxy: **{best.run_name}** ({best.quality_score or 0:.1f}/10).",
                "- Quality is an offline heuristic; add peer-review scores for submission.",
                "- Multi-agent adds handoff/token overhead; use it when decomposition or "
                "independent verification creates measurable value.",
                "",
                "## Failure mode and mitigation",
                "",
                "An unsupported claim can propagate through shared state and look like consensus. "
                "Keep source IDs at handoffs, validate citations, cap iterations, and inspect "
                "the JSON traces before accepting the final answer.",
            ]
        )
    return "\n".join(lines) + "\n"
