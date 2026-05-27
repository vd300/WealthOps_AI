import json
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

import asyncpg

from app.core.config import Settings
from app.models.documents import DocumentRecord, DocumentStatus, IngestionJobStatus


class DocumentRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def create_document(
        self,
        *,
        filename: str,
        content_type: str,
        uploaded_by: str,
        file_size_bytes: int,
    ) -> DocumentRecord:
        async with _connect(self._settings) as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO documents (
                    filename,
                    content_type,
                    status,
                    uploaded_by,
                    file_size_bytes
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                filename,
                content_type,
                DocumentStatus.UPLOADED.value,
                uploaded_by,
                file_size_bytes,
            )
        return _document_from_row(row)

    async def list_documents(self) -> list[DocumentRecord]:
        async with _connect(self._settings) as connection:
            rows = await connection.fetch(
                """
                SELECT *
                FROM documents
                ORDER BY created_at DESC
                """
            )
        return [_document_from_row(row) for row in rows]

    async def get_document(self, document_id: UUID) -> DocumentRecord | None:
        async with _connect(self._settings) as connection:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM documents
                WHERE id = $1
                """,
                document_id,
            )
        return _document_from_row(row) if row else None

    async def get_documents_by_ids(
        self,
        document_ids: list[UUID],
    ) -> list[DocumentRecord]:
        if not document_ids:
            return []

        async with _connect(self._settings) as connection:
            rows = await connection.fetch(
                """
                SELECT *
                FROM documents
                WHERE id = ANY($1::uuid[])
                """,
                document_ids,
            )
        return [_document_from_row(row) for row in rows]

    async def create_ingestion_job(self, document_id: UUID) -> UUID:
        async with _connect(self._settings) as connection:
            return await connection.fetchval(
                """
                INSERT INTO ingestion_jobs (document_id, status)
                VALUES ($1, $2)
                RETURNING id
                """,
                document_id,
                IngestionJobStatus.UPLOADED.value,
            )

    async def update_document_storage(
        self,
        *,
        document_id: UUID,
        bucket: str,
        object_key: str,
    ) -> DocumentRecord:
        async with _connect(self._settings) as connection:
            row = await connection.fetchrow(
                """
                UPDATE documents
                SET storage_bucket = $2,
                    object_key = $3,
                    updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                document_id,
                bucket,
                object_key,
            )
        return _document_from_row(row)

    async def mark_processing(self, *, document_id: UUID, job_id: UUID) -> None:
        async with _connect(self._settings) as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    UPDATE documents
                    SET status = $2, updated_at = now()
                    WHERE id = $1
                    """,
                    document_id,
                    DocumentStatus.PROCESSING.value,
                )
                await connection.execute(
                    """
                    UPDATE ingestion_jobs
                    SET status = $2, started_at = COALESCE(started_at, now()), updated_at = now()
                    WHERE id = $1
                    """,
                    job_id,
                    IngestionJobStatus.PROCESSING.value,
                )

    async def insert_chunks(
        self,
        *,
        document_id: UUID,
        chunks: list[dict[str, Any]],
        embedding_provider: str,
    ) -> None:
        async with _connect(self._settings) as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM document_chunks WHERE document_id = $1",
                    document_id,
                )
                await connection.executemany(
                    """
                    INSERT INTO document_chunks (
                        id,
                        document_id,
                        chunk_index,
                        content,
                        page_number,
                        qdrant_point_id,
                        embedding_provider,
                        metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    """,
                    [
                        (
                            chunk["id"],
                            document_id,
                            chunk["chunk_index"],
                            chunk["content"],
                            chunk.get("page_number"),
                            chunk["id"],
                            embedding_provider,
                            json.dumps(chunk.get("metadata", {})),
                        )
                        for chunk in chunks
                    ],
                )

    async def mark_indexed(
        self,
        *,
        document_id: UUID,
        job_id: UUID,
        chunk_count: int,
        extracted_char_count: int,
    ) -> DocumentRecord:
        async with _connect(self._settings) as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    UPDATE documents
                    SET status = $2,
                        chunk_count = $3,
                        extracted_char_count = $4,
                        error_message = NULL,
                        updated_at = now()
                    WHERE id = $1
                    RETURNING *
                    """,
                    document_id,
                    DocumentStatus.INDEXED.value,
                    chunk_count,
                    extracted_char_count,
                )
                await connection.execute(
                    """
                    UPDATE ingestion_jobs
                    SET status = $2,
                        error_message = NULL,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = $1
                    """,
                    job_id,
                    IngestionJobStatus.INDEXED.value,
                )
        return _document_from_row(row)

    async def mark_failed(
        self,
        *,
        document_id: UUID,
        job_id: UUID,
        error_message: str,
    ) -> DocumentRecord:
        safe_message = error_message[:1000]
        async with _connect(self._settings) as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    UPDATE documents
                    SET status = $2,
                        error_message = $3,
                        updated_at = now()
                    WHERE id = $1
                    RETURNING *
                    """,
                    document_id,
                    DocumentStatus.FAILED.value,
                    safe_message,
                )
                await connection.execute(
                    """
                    UPDATE ingestion_jobs
                    SET status = $2,
                        error_message = $3,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = $1
                    """,
                    job_id,
                    IngestionJobStatus.FAILED.value,
                    safe_message,
                )
        return _document_from_row(row)


@asynccontextmanager
async def _connect(settings: Settings):
    connection = await asyncpg.connect(settings.database_url)
    try:
        yield connection
    finally:
        await connection.close()


def _document_from_row(row: asyncpg.Record) -> DocumentRecord:
    return DocumentRecord.model_validate(dict(row))
