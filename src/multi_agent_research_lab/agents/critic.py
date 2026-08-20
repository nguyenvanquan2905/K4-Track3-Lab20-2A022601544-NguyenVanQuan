"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate that the final answer cites every collected source."""

        answer = state.final_answer or ""
        missing = [
            str(index) for index in range(1, len(state.sources) + 1) if f"[{index}]" not in answer
        ]
        if not answer:
            finding = "Critic: final answer is missing."
            state.errors.append(finding)
        elif missing:
            finding = f"Critic: citations missing for sources {', '.join(missing)}."
            state.errors.append(finding)
        else:
            finding = "Critic: citation coverage check passed."
        state.add_trace_event("critic", {"finding": finding})
        return state
