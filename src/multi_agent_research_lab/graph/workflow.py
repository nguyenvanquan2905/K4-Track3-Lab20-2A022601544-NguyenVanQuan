"""LangGraph supervisor/worker workflow."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

Node = Callable[[ResearchState], dict[str, Any]]


class MultiAgentWorkflow:
    """Build and execute a real LangGraph conditional workflow."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._deadline: float | None = None
        self.supervisor = SupervisorAgent(self.settings)
        self.workers: dict[str, BaseAgent] = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

    @staticmethod
    def _dump(state: ResearchState) -> dict[str, Any]:
        return state.model_dump()

    def _supervisor_node(self, state: ResearchState) -> dict[str, Any]:
        if self._deadline is not None and perf_counter() >= self._deadline:
            state.errors.append("Workflow timeout exceeded")
            state.record_route("done")
            return self._dump(state)
        self.supervisor.run(state)
        return self._dump(state)

    def _worker_node(self, worker: BaseAgent) -> Node:
        def run(state: ResearchState) -> dict[str, Any]:
            try:
                with trace_span(
                    worker.name,
                    {"iteration": state.iteration},
                    settings=self.settings,
                ) as span:
                    worker.run(state)
                state.add_trace_event("span", span)
            except Exception as exc:
                state.errors.append(f"{worker.name}: {type(exc).__name__}: {exc}")
            return self._dump(state)

        return run

    @staticmethod
    def _next_route(state: ResearchState) -> str:
        return state.route_history[-1]

    def build(self) -> Any:
        """Compile Supervisor and workers into a conditional StateGraph."""

        graph: Any = StateGraph(ResearchState)
        graph.add_node("supervisor", self._supervisor_node)
        for name, worker in self.workers.items():
            graph.add_node(name, self._worker_node(worker))
            graph.add_edge(name, "supervisor")
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._next_route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )
        return graph.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Invoke LangGraph with a recursion guard and validate the final state."""

        recursion_limit = self.settings.max_iterations * 2 + 2
        self._deadline = perf_counter() + self.settings.timeout_seconds
        try:
            result = self.build().invoke(state, config={"recursion_limit": recursion_limit})
            return ResearchState.model_validate(result)
        finally:
            self._deadline = None
