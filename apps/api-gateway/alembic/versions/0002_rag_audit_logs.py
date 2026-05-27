"""create rag audit logs table

Revision ID: 0002_rag_audit_logs
Revises: 0001_document_ingestion
Create Date: 2026-05-27
"""

from alembic import op

revision = "0002_rag_audit_logs"
down_revision = "0001_document_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rag_audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id TEXT NOT NULL,
            request_id TEXT,
            question TEXT NOT NULL,
            retrieved_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            llm_provider TEXT NOT NULL,
            llm_model TEXT NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            latency_ms INTEGER NOT NULL,
            response_status TEXT NOT NULL,
            compliance_status TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_created_at ON rag_audit_logs (created_at)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_user_id ON rag_audit_logs (user_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_response_status ON rag_audit_logs (response_status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rag_audit_logs")
