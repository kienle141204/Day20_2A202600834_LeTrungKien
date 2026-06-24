"""Critic agent: reviews the final answer and flags issues for revision."""

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class CriticAgent(BaseAgent):
    """Fact-checking and quality-review agent driving the revision loop."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate the final answer and record findings for the Supervisor to act on."""

        findings: list[str] = []
        if not state.final_answer:
            findings.append("No final answer produced.")
        else:
            if state.sources:
                cited = {int(n) for n in _CITATION_PATTERN.findall(state.final_answer)}
                valid_cited = {n for n in cited if 1 <= n <= len(state.sources)}
                if not valid_cited:
                    findings.append(
                        "Final answer does not cite any of the numbered sources ([n])."
                    )
            if len(state.final_answer.split()) < 20:
                findings.append("Final answer seems too short to be substantive.")

        state.critic_findings = findings
        state.critic_passed = not findings

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content="; ".join(findings) if findings else "No issues found.",
                metadata={"issue_count": len(findings)},
            )
        )
        state.add_trace_event("critic", {"issue_count": len(findings)})
        return state
