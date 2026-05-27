from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import logging
from time import perf_counter
from typing import Any

import httpx
from pydantic import SecretStr

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


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
            total_tokens=len(prompt.split()) + len(answer.split()),
        )


class LLMProviderError(RuntimeError):
    pass


class OpenAICompatibleLLMClient(LLMClient):
    provider = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        if _is_missing_real_api_key(api_key):
            raise ValueError("LLM_API_KEY is required when LLM_PROVIDER=openai")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/") or "https://api.openai.com/v1"
        self.model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse:
        request_model = model or self.model
        payload = {
            "model": request_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = await self._post_chat_completion(
            url=f"{self._base_url}/chat/completions",
            payload=payload,
            headers=headers,
            model=request_model,
        )
        return _parse_chat_completion(data, provider=self.provider, fallback_model=request_model)

    async def _post_chat_completion(
        self,
        *,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        model: str,
    ) -> dict[str, Any]:
        attempts = self._max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            started_at = perf_counter()
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                latency_ms = int((perf_counter() - started_at) * 1000)
                logger.info(
                    "llm_request_completed",
                    extra={
                        "llm_provider": self.provider,
                        "llm_model": model,
                        "latency_ms": latency_ms,
                        "attempt": attempt,
                    },
                )
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status_code = exc.response.status_code
                latency_ms = int((perf_counter() - started_at) * 1000)
                failure_reason = f"http_{status_code}"
                logger.warning(
                    "llm_request_failed",
                    extra={
                        "llm_provider": self.provider,
                        "llm_model": model,
                        "latency_ms": latency_ms,
                        "attempt": attempt,
                        "failure_reason": failure_reason,
                    },
                )
                if status_code < 500 and status_code != 429:
                    break
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_error = exc
                latency_ms = int((perf_counter() - started_at) * 1000)
                logger.warning(
                    "llm_request_failed",
                    extra={
                        "llm_provider": self.provider,
                        "llm_model": model,
                        "latency_ms": latency_ms,
                        "attempt": attempt,
                        "failure_reason": exc.__class__.__name__,
                    },
                )

            if attempt < attempts:
                await asyncio.sleep(min(0.25 * attempt, 1.0))

        reason = last_error.__class__.__name__ if last_error else "unknown"
        raise LLMProviderError(f"LLM provider request failed: {reason}") from last_error


class AzureOpenAICompatibleLLMClient(OpenAICompatibleLLMClient):
    provider = "azure_openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        api_version: str,
    ) -> None:
        if not base_url:
            raise ValueError("LLM_BASE_URL is required when LLM_PROVIDER=azure_openai")
        if _is_missing_real_api_key(api_key):
            raise ValueError("LLM_API_KEY is required when LLM_PROVIDER=azure_openai")
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self._api_version = api_version

    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse:
        deployment = model or self.model
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        headers = {"api-key": self._api_key}
        url = (
            f"{self._base_url}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={self._api_version}"
        )
        data = await self._post_chat_completion(
            url=url,
            payload=payload,
            headers=headers,
            model=deployment,
        )
        return _parse_chat_completion(data, provider=self.provider, fallback_model=deployment)


def create_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    api_key = _secret_value(settings.llm_api_key)
    if provider in {"mock", "local"}:
        return MockLLMClient(settings.llm_model)

    if provider == "openai":
        return OpenAICompatibleLLMClient(
            api_key=api_key,
            base_url=settings.llm_base_url or "https://api.openai.com/v1",
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    if provider == "azure_openai":
        return AzureOpenAICompatibleLLMClient(
            api_key=api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            api_version=settings.azure_openai_api_version,
        )

    raise ValueError(
        "Unsupported LLM_PROVIDER. Expected one of: mock, openai, azure_openai."
    )


def _secret_value(secret: SecretStr) -> str:
    return secret.get_secret_value()


def _is_missing_real_api_key(api_key: str) -> bool:
    normalized = api_key.strip().lower()
    return (
        not normalized
        or "replace-with" in normalized
        or normalized == "local-development-placeholder"
    )


def _parse_chat_completion(
    data: dict[str, Any],
    *,
    provider: str,
    fallback_model: str,
) -> LLMResponse:
    choices = data.get("choices") or []
    if not choices:
        raise LLMProviderError("LLM provider returned no choices")

    message = choices[0].get("message") or {}
    text = str(message.get("content") or "").strip()
    if not text:
        raise LLMProviderError("LLM provider returned an empty response")

    usage = data.get("usage") or {}
    return LLMResponse(
        text=text,
        provider=provider,
        model=str(data.get("model") or fallback_model),
        prompt_tokens=_optional_int(usage.get("prompt_tokens")),
        completion_tokens=_optional_int(usage.get("completion_tokens")),
        total_tokens=_optional_int(usage.get("total_tokens")),
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
