"""Optional critic agent for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        findings: list[str] = []
        if not state.final_answer:
            findings.append("No final answer produced.")
        else:
            cited_sources = sum(
                1 for s in state.sources if s.url and s.url in (state.final_answer or "")
            )
            if state.sources and cited_sources == 0:
                findings.append("Final answer does not reference any collected source URLs.")
            if len(state.final_answer.split()) < 20:
                findings.append("Final answer seems too short to be substantive.")

        if findings:
            state.errors.extend(findings)

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content="; ".join(findings) if findings else "No issues found.",
                metadata={"issue_count": len(findings)},
            )
        )
        state.add_trace_event("critic", {"issue_count": len(findings)})
        return state
