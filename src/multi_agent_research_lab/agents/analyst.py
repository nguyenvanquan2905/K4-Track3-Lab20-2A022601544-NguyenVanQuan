"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Extract source-backed claims and flag evidence limitations."""

        if not state.sources:
            state.errors.append("Analyst received no sources")
            state.analysis_notes = "Insufficient evidence for analysis."
        else:
            claims = [
                f"- Source [{index}] supports: {source.snippet[:260].rstrip()}"
                for index, source in enumerate(state.sources, 1)
            ]
            state.analysis_notes = (
                "Evidence synthesis\n"
                + "\n".join(claims)
                + "\nCaution: local corpus excerpts should be verified before high-stakes use."
            )
        state.agent_results.append(
            AgentResult(agent=AgentName.ANALYST, content=state.analysis_notes)
        )
        state.add_trace_event("analyst", {"source_count": len(state.sources)})
        return state
