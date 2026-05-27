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
);

CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_created_at ON rag_audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_user_id ON rag_audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_response_status ON rag_audit_logs (response_status);
