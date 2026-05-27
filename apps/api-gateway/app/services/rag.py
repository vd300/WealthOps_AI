from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from app.core.config import Settings
from app.db.rag import RAGAuditRepository
from app.models.rag import (
    ComplianceStatus,
    RAGCitation,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGResponseStatus,
    RetrievedChunkSummary,
)
from app.services.embeddings import EmbeddingProvider, create_embedding_provider
from app.services.llm import LLMClient, create_llm_client
from app.services.vector_store import QdrantVectorStore, RetrievedChunk


INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough retrieved context to answer this question."
)


@dataclass(frozen=True)
class RAGPrompt:
    prompt: str
    context: str


class RAGPromptBuilder:
    def build(self, *, question: str, chunks: list[RetrievedChunk]) -> RAGPrompt:
        if not chunks:
            return RAGPrompt(
                prompt=(
                    "You are a financial document assistant. The retrieved context is empty. "
                    "Respond only that there is insufficient context."
                ),
                context="",
            )

        context_parts = []
        for index, chunk in enumerate(chunks, start=1):
            page = f", page {chunk.page_number}" if chunk.page_number is not None else ""
            context_parts.append(
                f"[{index}] document_id={chunk.document_id}, chunk_id={chunk.chunk_id}{page}\n"
                f"{chunk.content}"
            )

        context = "\n\n".join(context_parts)
        prompt = (
            "You are a financial document assistant. Answer the user's question using only "
            "the retrieved context below. Do not use outside knowledge. If the answer is not "
            "supported by the context, say there is insufficient context. Include citations "
            "by referring to the provided context numbers.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return RAGPrompt(prompt=prompt, context=context)


class RAGCitationBuilder:
    def build(self, chunks: list[RetrievedChunk]) -> list[RAGCitation]:
        citations: list[RAGCitation] = []
        seen: set[UUID] = set()
        for chunk in chunks:
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            citations.append(
                RAGCitation(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    page_number=chunk.page_number,
                    filename=chunk.filename,
                )
            )
        return citations


class RAGQueryService:
    def __init__(
        self,
        *,
        settings: Settings,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: QdrantVectorStore | None = None,
        llm_client: LLMClient | None = None,
        audit_repository: RAGAuditRepository | None = None,
        prompt_builder: RAGPromptBuilder | None = None,
        citation_builder: RAGCitationBuilder | None = None,
    ) -> None:
        self._settings = settings
        self._embedding_provider = embedding_provider or create_embedding_provider(settings)
        self._vector_store = vector_store or QdrantVectorStore(settings)
        self._llm_client = llm_client or create_llm_client(settings)
        self._audit_repository = audit_repository or RAGAuditRepository(settings)
        self._prompt_builder = prompt_builder or RAGPromptBuilder()
        self._citation_builder = citation_builder or RAGCitationBuilder()

    async def query(
        self,
        *,
        request: RAGQueryRequest,
        user_id: str,
        request_id: str | None,
    ) -> RAGQueryResponse:
        started_at = perf_counter()
        query_vector = (await self._embedding_provider.embed_texts([request.question]))[0]
        chunks = await self._vector_store.search_chunks(
            query_vector=query_vector,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )

        if not chunks:
            response = RAGQueryResponse(
                answer=INSUFFICIENT_CONTEXT_ANSWER,
                citations=[],
                confidence_score=0.0,
                retrieved_chunks=[],
                status=RAGResponseStatus.INSUFFICIENT_CONTEXT,
                compliance_status=ComplianceStatus.NEEDS_REVIEW,
                llm_provider=self._llm_client.provider,
                llm_model=self._llm_client.model,
            )
            await self._audit(response, request, chunks, user_id, request_id, started_at, None)
            return response

        prompt = self._prompt_builder.build(question=request.question, chunks=chunks)
        llm_response = await self._llm_client.generate(
            prompt.prompt,
            model=self._settings.llm_model,
        )
        citations = self._citation_builder.build(chunks)
        response = RAGQueryResponse(
            answer=llm_response.text,
            citations=citations,
            confidence_score=_confidence_score(chunks),
            retrieved_chunks=[_chunk_summary(chunk) for chunk in chunks],
            status=RAGResponseStatus.ANSWERED,
            compliance_status=ComplianceStatus.SAFE if citations else ComplianceStatus.NEEDS_REVIEW,
            llm_provider=llm_response.provider,
            llm_model=llm_response.model,
        )
        await self._audit(response, request, chunks, user_id, request_id, started_at, llm_response)
        return response

    async def _audit(
        self,
        response: RAGQueryResponse,
        request: RAGQueryRequest,
        chunks: list[RetrievedChunk],
        user_id: str,
        request_id: str | None,
        started_at: float,
        llm_response,
    ) -> None:
        latency_ms = int((perf_counter() - started_at) * 1000)
        await self._audit_repository.create_rag_audit_log(
            user_id=user_id,
            request_id=request_id,
            question=request.question,
            document_ids=request.document_ids or [],
            retrieved_chunk_ids=[chunk.chunk_id for chunk in chunks],
            llm_provider=response.llm_provider,
            llm_model=response.llm_model,
            prompt_tokens=getattr(llm_response, "prompt_tokens", None),
            completion_tokens=getattr(llm_response, "completion_tokens", None),
            latency_ms=latency_ms,
            response_status=response.status.value,
            compliance_status=response.compliance_status.value,
        )


def _confidence_score(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0
    average = sum(max(0.0, chunk.score) for chunk in chunks) / len(chunks)
    return round(min(1.0, average), 4)


def _chunk_summary(chunk: RetrievedChunk) -> RetrievedChunkSummary:
    preview = " ".join(chunk.content.split())
    if len(preview) > 220:
        preview = preview[:217].rstrip() + "..."
    return RetrievedChunkSummary(
        document_id=chunk.document_id,
        chunk_id=chunk.chunk_id,
        chunk_index=chunk.chunk_index,
        page_number=chunk.page_number,
        filename=chunk.filename,
        score=round(chunk.score, 4),
        preview=preview,
    )
