from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90",
                    "filename": "phase2-sample.txt",
                    "content_type": "text/plain",
                    "status": "INDEXED",
                    "uploaded_by": "analyst-1",
                    "file_size_bytes": 128,
                    "storage_bucket": "wealthops-documents",
                    "object_key": "documents/5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90/phase2-sample.txt",
                    "chunk_count": 3,
                    "extracted_char_count": 192,
                    "error_message": None,
                    "created_at": "2026-05-27T12:00:00Z",
                    "updated_at": "2026-05-27T12:00:03Z",
                }
            ]
        },
    )


class DocumentUploadResponse(BaseModel):
    document: DocumentRecord
    ingestion_job_id: UUID
    document_id: UUID | None = Field(
        default=None,
        description="UUID used by APIs such as POST /rag/query.",
        examples=["5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90"],
    )
    filename: str | None = Field(
        default=None,
        examples=["phase2-sample.txt"],
    )
    status: DocumentStatus | None = Field(
        default=None,
        examples=[DocumentStatus.INDEXED],
    )
    chunk_count: int | None = Field(
        default=None,
        description="Number of indexed chunks when ingestion has completed.",
        examples=[3],
    )

    @model_validator(mode="after")
    def populate_document_summary(self) -> "DocumentUploadResponse":
        self.document_id = self.document_id or self.document.id
        self.filename = self.filename or self.document.filename
        self.status = self.status or self.document.status
        self.chunk_count = self.chunk_count if self.chunk_count is not None else self.document.chunk_count
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document_id": "5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90",
                    "filename": "phase2-sample.txt",
                    "status": "INDEXED",
                    "chunk_count": 3,
                    "ingestion_job_id": "7bd2a940-9b8e-44d5-91b7-f79a6c841d15",
                    "document": {
                        "id": "5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90",
                        "filename": "phase2-sample.txt",
                        "content_type": "text/plain",
                        "status": "INDEXED",
                        "uploaded_by": "analyst-1",
                        "file_size_bytes": 128,
                        "storage_bucket": "wealthops-documents",
                        "object_key": "documents/5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90/phase2-sample.txt",
                        "chunk_count": 3,
                        "extracted_char_count": 192,
                        "error_message": None,
                        "created_at": "2026-05-27T12:00:00Z",
                        "updated_at": "2026-05-27T12:00:03Z",
                    },
                }
            ]
        }
    )


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {
                            "id": "5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90",
                            "filename": "phase2-sample.txt",
                            "content_type": "text/plain",
                            "status": "INDEXED",
                            "uploaded_by": "analyst-1",
                            "file_size_bytes": 128,
                            "storage_bucket": "wealthops-documents",
                            "object_key": "documents/5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90/phase2-sample.txt",
                            "chunk_count": 3,
                            "extracted_char_count": 192,
                            "error_message": None,
                            "created_at": "2026-05-27T12:00:00Z",
                            "updated_at": "2026-05-27T12:00:03Z",
                        }
                    ]
                }
            ]
        }
    )
