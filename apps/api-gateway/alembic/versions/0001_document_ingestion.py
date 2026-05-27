"""create document ingestion tables

Revision ID: 0001_document_ingestion
Revises:
Create Date: 2026-05-27
"""

from alembic import op

revision = "0001_document_ingestion"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('UPLOADED', 'PROCESSING', 'INDEXED', 'FAILED')),
            uploaded_by TEXT NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            storage_bucket TEXT,
            object_key TEXT,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            extracted_char_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents (uploaded_by)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            page_number INTEGER,
            qdrant_point_id UUID NOT NULL,
            embedding_provider TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (document_id, chunk_index)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks (document_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_page_number ON document_chunks (page_number)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK (status IN ('UPLOADED', 'PROCESSING', 'INDEXED', 'FAILED')),
            error_message TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_document_id ON ingestion_jobs (document_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs (status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion_jobs")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS documents")
