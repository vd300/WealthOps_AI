from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import SecretStr

from app.core.config import Settings


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMClient(ABC):
    provider: str
    model: str

    @abstractmethod
    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    provider = "mock"

    def __init__(self, model: str = "mock-rag-local") -> None:
        self.model = model

    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse:
        context = _extract_context(prompt)
        answer = _summarize_context(context)
        return LLMResponse(
            text=answer,
            provider=self.provider,
            model=model or self.model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(answer.split()),
        )


def create_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    api_key = _secret_value(settings.llm_api_key)
    if provider in {"mock", "local"} or not api_key or "replace-with" in api_key:
        return MockLLMClient(settings.llm_model)

    # Phase 3 defines the provider boundary and keeps unsupported real providers
    # behind the same local fallback until their API adapters are added later.
    return MockLLMClient(settings.llm_model)


def _secret_value(secret: SecretStr) -> str:
    return secret.get_secret_value()


def _extract_context(prompt: str) -> str:
    marker = "Context:"
    question_marker = "Question:"
    if marker not in prompt:
        return ""
    context = prompt.split(marker, 1)[1]
    if question_marker in context:
        context = context.split(question_marker, 1)[0]
    return context.strip()


def _summarize_context(context: str) -> str:
    lines = [line.strip() for line in context.splitlines() if line.strip()]
    content_lines = [line for line in lines if not line.startswith("[")]
    if not content_lines:
        return "I do not have enough retrieved context to answer this question."

    summary = " ".join(content_lines)
    if len(summary) > 700:
        summary = summary[:697].rstrip() + "..."
    return f"Based on the retrieved context: {summary}"
