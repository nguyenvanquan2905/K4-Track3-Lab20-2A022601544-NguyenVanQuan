"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Synthesize a clear response with numbered source references."""

        evidence = state.analysis_notes or state.research_notes or "No evidence was collected."
        references = "\n".join(
            f"[{index}] {source.title} — {source.url or 'local corpus'}"
            for index, source in enumerate(state.sources, 1)
        )
        state.final_answer = (
            f"# Research answer\n\n**Question:** {state.request.query}\n\n"
            f"## Findings\n\n{evidence}\n\n## Sources\n\n{references or 'No sources.'}"
        )
        state.agent_results.append(AgentResult(agent=AgentName.WRITER, content=state.final_answer))
        state.add_trace_event("writer", {"citation_count": len(state.sources)})
        return state
