"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


def _run_baseline(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    sources = SearchClient().search(query, request.max_sources)
    evidence = "\n".join(
        f"[{index}] {source.title}: {source.snippet}" for index, source in enumerate(sources, 1)
    )
    response = LLMClient().complete(
        "You are a concise single-agent research assistant. Preserve numbered citations.",
        f"Question: {query}\nEvidence:\n{evidence}",
    )
    state.sources = sources
    state.final_answer = response.content
    state.add_trace_event(
        "usage",
        {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
        },
    )
    return state


def _run_multi(query: str) -> ResearchState:
    return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=query)))


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline."""

    _init()
    _parse_query(query)
    state = _run_baseline(query)
    console.print(
        Panel.fit(state.final_answer or "No answer generated.", title="Single-Agent Baseline")
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=_parse_query(query))
    result = MultiAgentWorkflow().run(state)
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")] = (
        "Compare single-agent and multi-agent research workflows"
    ),
) -> None:
    """Benchmark both workflows and write Markdown plus JSON trace artifacts."""

    _init()
    _parse_query(query)
    baseline_state, baseline_metrics = run_benchmark("baseline", query, _run_baseline)
    multi_state, multi_metrics = run_benchmark("multi-agent", query, _run_multi)
    store = LocalArtifactStore()
    report_path = store.write_text(
        "benchmark_report.md", render_markdown_report([baseline_metrics, multi_metrics])
    )
    store.write_text("baseline_trace.json", baseline_state.model_dump_json(indent=2))
    store.write_text("multi_agent_trace.json", multi_state.model_dump_json(indent=2))
    console.print(Panel.fit(str(report_path.resolve()), title="Benchmark complete"))


if __name__ == "__main__":
    app()
