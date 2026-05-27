from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class IngestionJobStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class DocumentRecord(BaseModel):
    id: UUID
    filename: str
    content_type: str
    status: DocumentStatus
    uploaded_by: str
    file_size_bytes: int
    storage_bucket: str | None = None
    object_key: str | None = None
    chunk_count: int = 0
    extracted_char_count: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document: DocumentRecord
    ingestion_job_id: UUID
