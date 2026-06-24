"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from collections.abc import Callable
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import Settings, get_settings

# Rough placeholder pricing for the mock backend (USD per 1k tokens).
_MOCK_INPUT_COST_PER_1K = 0.0005
_MOCK_OUTPUT_COST_PER_1K = 0.0015

# Published OpenAI pricing (USD per 1M tokens) for models this lab is expected to use.
_OPENAI_PRICE_PER_1M_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


def _estimate_openai_cost(
    model: str, input_tokens: int | None, output_tokens: int | None
) -> float | None:
    pricing = _OPENAI_PRICE_PER_1M_TOKENS.get(model)
    if pricing is None or input_tokens is None or output_tokens is None:
        return None
    input_price, output_price = pricing
    return input_tokens / 1_000_000 * input_price + output_tokens / 1_000_000 * output_price


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client.

    Uses a deterministic mock backend by default so the lab runs without any API key.
    When `settings.openai_api_key` is set, a real provider call can be wired in via
    `_complete_openai` without changing the agent-facing interface.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Retry/timeout/token accounting live here, not in agents.
        """

        if self._settings.openai_api_key:
            return self._complete_with_retry(self._complete_openai, system_prompt, user_prompt)
        return self._complete_with_retry(self._complete_mock, system_prompt, user_prompt)

    def _complete_with_retry(
        self,
        fn: Callable[[str, str], LLMResponse],
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.1, max=2))
        def _call() -> LLMResponse:
            return fn(system_prompt, user_prompt)

        return _call()

    def _complete_mock(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Deterministic offline backend: synthesizes a structured response from the prompts."""

        content = (
            f"[mock-llm response]\n"
            f"System guidance: {system_prompt.strip()}\n"
            f"Synthesis of input: {user_prompt.strip()[:500]}"
        )
        input_tokens = len(system_prompt.split()) + len(user_prompt.split())
        output_tokens = len(content.split())
        cost_usd = (
            input_tokens / 1000 * _MOCK_INPUT_COST_PER_1K
            + output_tokens / 1000 * _MOCK_OUTPUT_COST_PER_1K
        )
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )

    def _complete_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Real OpenAI-backed completion.

        Seam for connecting an actual provider once `OPENAI_API_KEY` is configured.
        """

        from openai import OpenAI

        client = OpenAI(api_key=self._settings.openai_api_key)
        response = client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost_usd = _estimate_openai_cost(self._settings.openai_model, input_tokens, output_tokens)
        return LLMResponse(
            content=choice,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
