import logging
from functools import partial
from pathlib import Path

from anyio import to_thread
from fastapi import UploadFile

from app.core.config import Settings
from app.db.documents import DocumentRepository
from app.db.migrations import run_migrations
from app.models.documents import DocumentUploadResponse
from app.services.chunking import DocumentChunker
from app.services.document_validation import read_limited_upload, validate_upload_metadata
from app.services.embeddings import create_embedding_provider
from app.services.object_storage import ObjectStorageClient
from app.services.text_extraction import extract_text_pages, flatten_pages
from app.services.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: DocumentRepository | None = None,
        storage: ObjectStorageClient | None = None,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._storage = storage
        self._vector_store = vector_store
        self._embedding_provider = create_embedding_provider(settings)
        self._chunker = DocumentChunker(
            chunk_size=settings.document_chunk_size,
            chunk_overlap=settings.document_chunk_overlap,
        )

    async def ingest_upload(
        self,
        *,
        file: UploadFile,
        uploaded_by: str,
    ) -> DocumentUploadResponse:
        validate_upload_metadata(file)
        data = await read_limited_upload(file, self._settings.document_max_file_size_bytes)
        filename = Path(file.filename or "uploaded-document").name
        content_type = file.content_type or "application/octet-stream"

        repository = self._repository or DocumentRepository(self._settings)
        storage = self._storage or ObjectStorageClient(self._settings)
        vector_store = self._vector_store or QdrantVectorStore(self._settings)

        await run_migrations(self._settings)
        document = await repository.create_document(
            filename=filename,
            content_type=content_type,
            uploaded_by=uploaded_by,
            file_size_bytes=len(data),
        )
        job_id = await repository.create_ingestion_job(document.id)
        object_key = f"documents/{document.id}/{filename}"

        try:
            await to_thread.run_sync(
                partial(
                    storage.put_object,
                    object_key=object_key,
                    data=data,
                    content_type=content_type,
                )
            )
            await repository.update_document_storage(
                document_id=document.id,
                bucket=storage.bucket,
                object_key=object_key,
            )
            await repository.mark_processing(document_id=document.id, job_id=job_id)

            pages = extract_text_pages(filename, data)
            extracted_text = flatten_pages(pages)
            chunks = [chunk.to_record() for chunk in self._chunker.chunk_pages(pages)]
            if not chunks:
                raise ValueError("Document did not produce any indexable chunks.")

            vectors = await self._embedding_provider.embed_texts(
                [chunk["content"] for chunk in chunks]
            )
            await vector_store.ensure_collection()
            await vector_store.upsert_chunks(
                document_id=document.id,
                filename=filename,
                chunks=chunks,
                vectors=vectors,
            )
            await repository.insert_chunks(
                document_id=document.id,
                chunks=chunks,
                embedding_provider=self._embedding_provider.name,
            )
            final_document = await repository.mark_indexed(
                document_id=document.id,
                job_id=job_id,
                chunk_count=len(chunks),
                extracted_char_count=len(extracted_text),
            )
        except Exception as exc:
            logger.exception("document_ingestion_failed", extra={"document_id": document.id})
            final_document = await repository.mark_failed(
                document_id=document.id,
                job_id=job_id,
                error_message=str(exc),
            )

        return DocumentUploadResponse(document=final_document, ingestion_job_id=job_id)
