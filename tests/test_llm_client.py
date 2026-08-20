from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.services.llm_client import LLMClient


def test_google_provider_takes_precedence_over_openai() -> None:
    settings = Settings(
        google_api_key="google-test-key",
        google_model="gemini-test-model",
        openai_api_key="openai-test-key",
    )
    provider = LLMClient(settings)._provider_config()
    assert provider == (
        "google-test-key",
        "gemini-test-model",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def test_llm_client_falls_back_offline_without_keys() -> None:
    settings = Settings(google_api_key=None, openai_api_key=None)
    response = LLMClient(settings).complete("Summarize.", "Offline evidence")
    assert response.content == "Offline evidence"
    assert response.cost_usd == 0.0
