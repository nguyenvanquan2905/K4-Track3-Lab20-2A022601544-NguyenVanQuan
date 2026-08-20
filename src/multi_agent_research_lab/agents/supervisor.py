"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Route to the first missing artifact, enforcing the iteration limit."""

        if state.iteration >= self.settings.max_iterations:
            route = "done"
            if not state.final_answer:
                state.errors.append("Stopped after reaching max_iterations")
        elif not state.sources or not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        elif not state.final_answer:
            route = "writer"
        else:
            route = "done"
        state.record_route(route)
        state.add_trace_event("route", {"next": route, "iteration": state.iteration})
        return state

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
