from pathlib import Path
import os
import sys
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api-gateway"))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("OBJECT_STORAGE_URL", "http://localhost:9000")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "test")

from app.core.config import Settings
from app.main import create_app
from app.models.rag import RAGQueryRequest, RAGQueryResponse
from app.services.llm import MockLLMClient
from app.services.rag import RAGCitationBuilder, RAGPromptBuilder, RAGQueryService
from app.services.vector_store import QdrantVectorStore, RetrievedChunk


def test_prompt_builder_requires_context_grounding() -> None:
    chunk = _chunk(content="Liquidity risk is monitored through cash buffers.")

    prompt = RAGPromptBuilder().build(question="What is the liquidity risk?", chunks=[chunk])

    assert "using only the retrieved context" in prompt.prompt
    assert "Do not use outside knowledge" in prompt.prompt
    assert str(chunk.chunk_id) in prompt.prompt
    assert "Liquidity risk" in prompt.context


def test_prompt_builder_handles_empty_retrieval() -> None:
    prompt = RAGPromptBuilder().build(question="What is the revenue?", chunks=[])

    assert prompt.context == ""
    assert "insufficient context" in prompt.prompt


def test_citation_builder_uses_chunk_metadata() -> None:
    document_id = uuid4()
    chunk_id = uuid4()
    chunk = _chunk(document_id=document_id, chunk_id=chunk_id, page_number=3)

    citations = RAGCitationBuilder().build([chunk])

    assert len(citations) == 1
    assert citations[0].document_id == document_id
    assert citations[0].chunk_id == chunk_id
    assert citations[0].page_number == 3


@pytest.mark.asyncio
async def test_retriever_filters_by_document_ids(monkeypatch) -> None:
    captured_payload = {}
    document_id = uuid4()
    chunk_id = uuid4()

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "result": [
                    {
                        "id": str(chunk_id),
                        "score": 0.86,
                        "payload": {
                            "document_id": str(document_id),
                            "chunk_id": str(chunk_id),
                            "filename": "sample.txt",
                            "chunk_index": 2,
                            "page_number": 4,
                            "content": "Market risk increased.",
                        },
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json):
            captured_payload.update(json)
            return FakeResponse()

    monkeypatch.setattr("app.services.vector_store.httpx.AsyncClient", FakeAsyncClient)

    store = QdrantVectorStore(_settings())
    results = await store.search_chunks(
        query_vector=[0.1, 0.2],
        top_k=3,
        document_ids=[document_id],
    )

    assert captured_payload["limit"] == 3
    assert captured_payload["filter"]["must"][0]["match"]["any"] == [str(document_id)]
    assert results[0].document_id == document_id
    assert results[0].chunk_id == chunk_id


@pytest.mark.asyncio
async def test_rag_service_returns_insufficient_context_for_empty_retrieval() -> None:
    service = RAGQueryService(
        settings=_settings(),
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore([]),
        llm_client=MockLLMClient(),
        audit_repository=FakeAuditRepository(),
    )

    response = await service.query(
        request=RAGQueryRequest(question="What are the risks?", top_k=5),
        user_id="analyst-1",
        request_id="req-1",
    )

    assert response.status == "insufficient_context"
    assert response.confidence_score == 0
    assert response.citations == []
    assert "not have enough retrieved context" in response.answer


@pytest.mark.asyncio
async def test_rag_service_generates_answer_with_citations() -> None:
    chunk = _chunk(content="Revenue increased while liquidity risk remained monitored.")
    audit = FakeAuditRepository()
    service = RAGQueryService(
        settings=_settings(),
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore([chunk]),
        llm_client=MockLLMClient(),
        audit_repository=audit,
    )

    response = await service.query(
        request=RAGQueryRequest(question="What changed?", top_k=1),
        user_id="analyst-1",
        request_id="req-2",
    )

    assert response.status == "answered"
    assert response.confidence_score == 0.91
    assert response.citations[0].chunk_id == chunk.chunk_id
    assert response.retrieved_chunks[0].preview.startswith("Revenue increased")
    assert audit.entries[0]["retrieved_chunk_ids"] == [chunk.chunk_id]


def test_rag_query_endpoint_returns_typed_response(monkeypatch) -> None:
    document_id = uuid4()
    chunk_id = uuid4()

    class FakeRAGQueryService:
        def __init__(self, *, settings):
            self.settings = settings

        async def query(self, *, request, user_id, request_id):
            return RAGQueryResponse(
                answer="Liquidity risk is monitored.",
                citations=[
                    {
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "page_number": 1,
                        "filename": "sample.txt",
                    }
                ],
                confidence_score=0.8,
                retrieved_chunks=[
                    {
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "chunk_index": 0,
                        "page_number": 1,
                        "filename": "sample.txt",
                        "score": 0.8,
                        "preview": "Liquidity risk is monitored.",
                    }
                ],
                status="answered",
                compliance_status="SAFE",
                llm_provider="mock",
                llm_model="mock-rag-local",
            )

    monkeypatch.setattr("app.api.routes.RAGQueryService", FakeRAGQueryService)

    client = TestClient(_create_test_app())
    response = client.post(
        "/rag/query",
        json={"question": "What are the risks?", "top_k": 3},
        headers={"X-User-ID": "analyst-1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["citations"][0]["chunk_id"] == str(chunk_id)
    assert body["llm_provider"] == "mock"


class FakeEmbeddingProvider:
    name = "fake"
    dimensions = 2

    async def embed_texts(self, texts):
        return [[0.1, 0.2] for _ in texts]


class FakeVectorStore:
    def __init__(self, chunks):
        self.chunks = chunks

    async def search_chunks(self, *, query_vector, top_k, document_ids=None):
        return self.chunks[:top_k]


class FakeAuditRepository:
    def __init__(self):
        self.entries = []

    async def create_rag_audit_log(self, **kwargs):
        self.entries.append(kwargs)


def _chunk(
    *,
    document_id=None,
    chunk_id=None,
    content="Risk disclosure text.",
    score=0.91,
    page_number=1,
) -> RetrievedChunk:
    return RetrievedChunk(
        document_id=document_id or uuid4(),
        chunk_id=chunk_id or uuid4(),
        content=content,
        score=score,
        filename="sample.txt",
        chunk_index=0,
        page_number=page_number,
    )


def _create_test_app() -> FastAPI:
    return create_app(_settings())


def _settings(**overrides) -> Settings:
    values = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "OBJECT_STORAGE_URL": "http://localhost:9000",
        "JWT_SECRET": "test-secret",
        "LLM_PROVIDER": "mock",
        "LLM_API_KEY": "test-key",
        "LLM_MODEL": "mock-rag-local",
        "APP_ENV": "test",
    }
    values.update(overrides)
    return Settings(**values)
