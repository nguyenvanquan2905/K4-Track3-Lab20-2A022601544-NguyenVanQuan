from pathlib import Path

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.search_client import SearchClient


def test_supervisor_routes_missing_state_in_order() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    supervisor = SupervisorAgent()
    supervisor.run(state)
    assert state.route_history == ["researcher"]
    state.sources = [SourceDocument(title="Source", snippet="Evidence")]
    state.research_notes = "Evidence"
    supervisor.run(state)
    assert state.route_history[-1] == "analyst"
    state.analysis_notes = "Analysis"
    supervisor.run(state)
    assert state.route_history[-1] == "writer"
    state.final_answer = "Answer [1]"
    supervisor.run(state)
    assert state.route_history[-1] == "done"


def test_offline_search_returns_ranked_sources() -> None:
    root = Path("ai_agent_offline_research_corpus_v2/topics")
    results = SearchClient(root).search("multi agent shared state", 3)
    assert len(results) == 3
    assert all(item.metadata["source"] == "offline_corpus" for item in results)


def test_workflow_runs_end_to_end() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain shared state in multi-agent systems")
    )
    result = MultiAgentWorkflow(Settings(langsmith_api_key=None)).run(state)
    assert result.final_answer
    assert result.sources
    assert result.route_history == ["researcher", "analyst", "writer", "done"]
    assert not result.errors


def test_workflow_builds_langgraph_and_enforces_iteration_guard() -> None:
    workflow = MultiAgentWorkflow(Settings(max_iterations=1, langsmith_api_key=None))
    graph = workflow.build()
    assert {"supervisor", "researcher", "analyst", "writer"}.issubset(graph.get_graph().nodes)
    state = ResearchState(request=ResearchQuery(query="Explain agent routing guardrails"))
    result = workflow.run(state)
    assert result.route_history == ["researcher", "done"]
    assert "Stopped after reaching max_iterations" in result.errors
