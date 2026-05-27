from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RAGResponseStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class ComplianceStatus(StrEnum):
    SAFE = "SAFE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RAGQueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=4000,
        examples=["What risks are mentioned in this document?"],
    )
    document_ids: list[UUID] | None = Field(
        default=None,
        min_length=1,
        description=(
            "Optional list of document UUIDs from GET /documents. "
            "User interfaces can show filenames, but APIs use UUIDs internally."
        ),
        examples=[["5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90"]],
    )
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What risks are mentioned in this document?",
                    "document_ids": ["5f8c2e30-0b7a-4d3f-9a71-2f8e3a7b5c90"],
                    "top_k": 5,
                }
            ]
        }
    )


class RAGCitation(BaseModel):
    document_id: UUID
    chunk_id: UUID
    page_number: int | None = None
    filename: str | None = None


class RetrievedChunkSummary(BaseModel):
    document_id: UUID
    chunk_id: UUID
    chunk_index: int | None = None
    page_number: int | None = None
    filename: str | None = None
    score: float
    preview: str


class RAGQueryResponse(BaseModel):
    answer: str
    citations: list[RAGCitation]
    confidence_score: float = Field(ge=0.0, le=1.0)
    retrieved_chunks: list[RetrievedChunkSummary]
    status: RAGResponseStatus
    compliance_status: ComplianceStatus
    llm_provider: str
    llm_model: str
