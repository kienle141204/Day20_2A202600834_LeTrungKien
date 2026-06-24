"""Supervisor / router."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState

DONE = "done"


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` / `state.next_route` with the next route."""

        if state.iteration >= self._settings.max_iterations:
            next_route = DONE
        elif state.research_notes is None:
            next_route = "researcher"
        elif state.analysis_notes is None:
            next_route = "analyst"
        elif state.final_answer is None:
            next_route = "writer"
        elif state.critic_passed is None:
            next_route = "critic"
        elif state.critic_passed is False and state.revision_count < self._settings.max_revisions:
            state.revision_count += 1
            next_route = "writer"
        else:
            next_route = DONE

        state.next_route = next_route
        state.record_route(next_route)
        state.add_trace_event("route", {"next": next_route})
        return state
