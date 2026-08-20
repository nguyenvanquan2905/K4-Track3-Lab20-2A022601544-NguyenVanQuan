"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass

from multi_agent_research_lab.core.config import Settings, get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """OpenAI-compatible adapter for Gemini/OpenAI with an offline fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a completion; use the local fallback when no API key is configured."""

        provider = self._provider_config()
        if provider is None:
            content = self._offline_complete(system_prompt, user_prompt)
            return LLMResponse(
                content=content,
                input_tokens=self._estimate_tokens(system_prompt + user_prompt),
                output_tokens=self._estimate_tokens(content),
                cost_usd=0.0,
            )
        try:
            from openai import OpenAI, OpenAIError
        except ImportError:
            content = self._offline_complete(system_prompt, user_prompt)
            return LLMResponse(content=content, cost_usd=0.0)
        try:
            api_key, model, base_url = provider
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.settings.timeout_seconds,
                max_retries=2,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            usage = response.usage
            return LLMResponse(
                content=response.choices[0].message.content or "",
                input_tokens=usage.prompt_tokens if usage else None,
                output_tokens=usage.completion_tokens if usage else None,
            )
        except (OpenAIError, OSError, RuntimeError, ValueError):
            content = self._offline_complete(system_prompt, user_prompt)
            return LLMResponse(content=content, cost_usd=0.0)

    def _provider_config(self) -> tuple[str, str, str | None] | None:
        """Prefer Google AI Studio, then OpenAI, when credentials are configured."""

        if self.settings.google_api_key:
            return (
                self.settings.google_api_key,
                self.settings.google_model,
                self.settings.google_base_url,
            )
        if self.settings.openai_api_key:
            return self.settings.openai_api_key, self.settings.openai_model, None
        return None

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def _offline_complete(system_prompt: str, user_prompt: str) -> str:
        del system_prompt
        compact = " ".join(user_prompt.split())
        return compact[:4000]
