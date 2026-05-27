import hashlib
import math
from abc import ABC, abstractmethod

from app.core.config import Settings


class EmbeddingProvider(ABC):
    name: str
    dimensions: int

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProvider):
    name = "mock"

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        words = text.lower().split()
        for index, word in enumerate(words or [text]):
            digest = hashlib.sha256(f"{index}:{word}".encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider in {"mock", "local"}:
        return MockEmbeddingProvider(settings.embedding_dimensions)

    # Phase 2 keeps ingestion provider-agnostic and falls back locally when no
    # real embedding provider has been implemented/configured yet.
    return MockEmbeddingProvider(settings.embedding_dimensions)
