import json
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.db.documents import _connect
from app.db.migrations import run_migrations


class RAGAuditRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def create_rag_audit_log(
        self,
        *,
        user_id: str,
        request_id: str | None,
        question: str,
        document_ids: list[UUID],
        retrieved_chunk_ids: list[UUID],
        llm_provider: str,
        llm_model: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        latency_ms: int,
        response_status: str,
        compliance_status: str,
    ) -> None:
        await run_migrations(self._settings)
        metadata: dict[str, Any] = {
            "document_ids": [str(document_id) for document_id in document_ids],
            "retrieved_chunk_ids": [str(chunk_id) for chunk_id in retrieved_chunk_ids],
        }
        async with _connect(self._settings) as connection:
            await connection.execute(
                """
                INSERT INTO rag_audit_logs (
                    user_id,
                    request_id,
                    question,
                    retrieved_chunk_ids,
                    llm_provider,
                    llm_model,
                    prompt_tokens,
                    completion_tokens,
                    latency_ms,
                    response_status,
                    compliance_status,
                    metadata
                )
                VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
                """,
                user_id,
                request_id,
                question,
                json.dumps(metadata["retrieved_chunk_ids"]),
                llm_provider,
                llm_model,
                prompt_tokens,
                completion_tokens,
                latency_ms,
                response_status,
                compliance_status,
                json.dumps(metadata),
            )
