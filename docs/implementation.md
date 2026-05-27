# WealthOps AI — Implementation Notes

This file tracks how the project is implemented. Update it as tasks are completed.

## 1. Current Implementation Status

| Phase | Status |
|---|---|
| Phase 1: Foundation | Complete |
| Phase 2: Document Ingestion | Complete |
| Phase 3: RAG Q&A | Complete |
| Phase 3.5: Real LLM Provider Integration | Complete |
| Phase 4: Portfolio Intelligence | Not Started |
| Phase 5: Compliance | Not Started |
| Phase 6: Agentic Workflow | Not Started |
| Phase 7: Airflow | Not Started |
| Phase 8: Deployment | Not Started |
| Phase 9: Observability | Not Started |

## Phase 1 Implementation Summary

Phase 1 foundation is implemented.

Implemented:

- Monorepo folder structure from `docs/task.md`
- FastAPI API Gateway service
- `GET /health`
- `GET /ready`
- Structured JSON logging
- Request ID propagation through `X-Request-ID`
- Global exception handling with safe error responses
- Pydantic Settings configuration
- Required environment variables:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `QDRANT_URL`
  - `OBJECT_STORAGE_URL`
  - `JWT_SECRET`
  - `LLM_PROVIDER`
  - `LLM_API_KEY`
- Basic readiness checks for PostgreSQL, Redis, and Qdrant
- Docker Compose services:
  - `api-gateway`
  - `postgres`
  - `qdrant`
  - `redis`
  - `minio`
- Root README instructions for running and validating Phase 1
- Focused tests for health, readiness, and global exception handling

## Phase 2 Implementation Summary

Phase 2 document ingestion is implemented.

Implemented:

- `POST /documents/upload`
- Upload validation for PDF, TXT, CSV, and XLSX
- Configurable upload size limit through `DOCUMENT_MAX_FILE_SIZE_BYTES`
- Raw uploaded file storage in MinIO
- PostgreSQL metadata storage for documents, chunks, and ingestion jobs
- SQL migration file: `apps/api-gateway/migrations/0001_document_ingestion.sql`
- Alembic migration: `apps/api-gateway/alembic/versions/0001_document_ingestion.py`
- Lightweight migration runner applied before first document metadata write
- Text extraction for:
  - PDF via `pypdf`
  - TXT via UTF-8 decoding
  - CSV via Python CSV parsing
  - XLSX via `openpyxl`
- Configurable chunking through:
  - `DOCUMENT_CHUNK_SIZE`
  - `DOCUMENT_CHUNK_OVERLAP`
- Page number tracking in chunk metadata
- Provider-agnostic embedding interface
- Deterministic local/mock embedding provider for development and tests
- Qdrant collection creation and vector upsert for document chunks
- Qdrant payload metadata including document id, chunk id, filename, page number, and content
- Document and ingestion job status tracking:
  - `UPLOADED`
  - `PROCESSING`
  - `INDEXED`
  - `FAILED`
- Tests for document upload route behavior, file validation, text extraction, chunking, and failed status updates

The ingestion flow is synchronous in Phase 2 so local validation is straightforward. Background queues, retry workers, and scheduled ingestion are intentionally deferred to later phases.

## Phase 2 Files Created or Updated

- `apps/api-gateway/app/api/routes.py`
- `apps/api-gateway/app/core/config.py`
- `apps/api-gateway/app/db/__init__.py`
- `apps/api-gateway/app/db/documents.py`
- `apps/api-gateway/app/db/migrations.py`
- `apps/api-gateway/app/models/__init__.py`
- `apps/api-gateway/app/models/documents.py`
- `apps/api-gateway/app/services/chunking.py`
- `apps/api-gateway/app/services/document_ingestion.py`
- `apps/api-gateway/app/services/document_validation.py`
- `apps/api-gateway/app/services/embeddings.py`
- `apps/api-gateway/app/services/object_storage.py`
- `apps/api-gateway/app/services/text_extraction.py`
- `apps/api-gateway/app/services/vector_store.py`
- `apps/api-gateway/migrations/0001_document_ingestion.sql`
- `apps/api-gateway/alembic.ini`
- `apps/api-gateway/alembic/env.py`
- `apps/api-gateway/alembic/versions/0001_document_ingestion.py`
- `tests/test_document_ingestion.py`
- `tests/fixtures/sample.pdf`
- `apps/api-gateway/requirements.txt`
- `.env.example`
- `infra/docker-compose/docker-compose.yml`
- `README.md`

## Phase 3 Implementation Summary

Phase 3 RAG Q&A is implemented.

Implemented:

- `POST /rag/query`
- Typed RAG request and response models
- Question, optional `document_ids`, and configurable `top_k`
- Query embedding through the existing provider-agnostic embedding interface
- Qdrant vector retrieval from the Phase 2 `document_chunks` collection
- Optional Qdrant filtering by `document_ids`
- Context block construction from retrieved chunks
- Prompt builder that instructs the model to answer only from retrieved context
- Provider-agnostic `LLMClient` interface
- Mock/local LLM provider for development and tests
- Citation builder using retrieved chunk metadata
- Confidence score based on retrieved chunk scores
- Retrieved chunk summaries in the response
- Empty retrieval handling with an `insufficient_context` response
- RAG audit logging for question, retrieved chunks, provider/model, token usage when available, latency, response status, and compliance status
- SQL and Alembic migrations for `rag_audit_logs`
- Tests for retriever, prompt builder, citation builder, empty retrieval, service orchestration, and `/rag/query`

Phase 3 intentionally keeps compliance classification lightweight. Full prompt injection checks, PII checks, unsupported-claim detection, and financial advice classification remain Phase 5 work.

## Phase 3 Files Created or Updated

- `apps/api-gateway/app/api/routes.py`
- `apps/api-gateway/app/core/config.py`
- `apps/api-gateway/app/db/rag.py`
- `apps/api-gateway/app/models/rag.py`
- `apps/api-gateway/app/services/llm.py`
- `apps/api-gateway/app/services/rag.py`
- `apps/api-gateway/app/services/vector_store.py`
- `apps/api-gateway/migrations/0002_rag_audit_logs.sql`
- `apps/api-gateway/alembic/versions/0002_rag_audit_logs.py`
- `tests/test_rag.py`
- `.env.example`
- `infra/docker-compose/docker-compose.yml`
- `docs/task.md`
- `docs/implementation.md`
- `README.md`

## Phase 3 API Example

Request:

```json
{
  "question": "What are the key risks?",
  "document_ids": ["00000000-0000-0000-0000-000000000000"],
  "top_k": 5
}
```

Response:

```json
{
  "answer": "Based on the retrieved context: ...",
  "citations": [
    {
      "document_id": "00000000-0000-0000-0000-000000000000",
      "chunk_id": "11111111-1111-1111-1111-111111111111",
      "page_number": 1,
      "filename": "phase2-sample.txt"
    }
  ],
  "confidence_score": 0.82,
  "retrieved_chunks": [
    {
      "document_id": "00000000-0000-0000-0000-000000000000",
      "chunk_id": "11111111-1111-1111-1111-111111111111",
      "chunk_index": 0,
      "page_number": 1,
      "filename": "phase2-sample.txt",
      "score": 0.82,
      "preview": "WealthOps sample document..."
    }
  ],
  "status": "answered",
  "compliance_status": "SAFE",
  "llm_provider": "mock",
  "llm_model": "mock-rag-local"
}
```

Empty retrieval response:

```json
{
  "answer": "I do not have enough retrieved context to answer this question.",
  "citations": [],
  "confidence_score": 0.0,
  "retrieved_chunks": [],
  "status": "insufficient_context",
  "compliance_status": "NEEDS_REVIEW",
  "llm_provider": "mock",
  "llm_model": "mock-rag-local"
}
```

## Phase 3 Design Decisions

- Reused the Phase 2 embedding provider and Qdrant collection instead of changing ingestion architecture.
- Kept retrieval, prompt building, citation building, LLM generation, and audit persistence in separate modules.
- Used a mock LLM as the default provider so local development and tests do not require a real API key.
- Added the LLM provider boundary now, while leaving Azure OpenAI, OpenAI, AWS Bedrock, and local model server adapters for later.
- Returned `compliance_status` for API compatibility, but limited it to citation/context availability until Phase 5 guardrails are built.

## Phase 3 Validation Commands

Start Docker Compose:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Upload a sample document:

```powershell
curl.exe -X POST http://localhost:8000/documents/upload -H "X-Uploaded-By: analyst-1" -F "file=@samples/phase2-sample.txt;type=text/plain"
```

Check that the document is indexed:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT id, filename, status, chunk_count FROM documents ORDER BY created_at DESC LIMIT 5;"
```

Call `/rag/query`:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

Test `document_id` filtering by replacing `<DOCUMENT_ID>` with an indexed document id:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"document_ids\":[\"<DOCUMENT_ID>\"],\"top_k\":3}"
```

Test empty retrieval behavior with a random UUID:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"document_ids\":[\"00000000-0000-0000-0000-000000000000\"],\"top_k\":3}"
```

Check RAG audit logs:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT user_id, question, retrieved_chunk_ids, llm_provider, llm_model, latency_ms, response_status, compliance_status, created_at FROM rag_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

Run tests:

```bash
pytest
```

## Phase 3 Limitations

- Query rewriting, reranking, streaming responses, caching, and token cost estimation are not implemented.
- Access control for document-level permissions is not implemented.
- Compliance guardrails are limited to basic status fields until Phase 5.

## Phase 3.5 Implementation Summary

Phase 3.5 real LLM provider integration is implemented.

Implemented:

- Kept `MockLLMClient` as the default local and test provider.
- Added OpenAI-compatible chat completions support for `LLM_PROVIDER=openai`.
- Added Azure OpenAI-compatible chat completions support for `LLM_PROVIDER=azure_openai`.
- Added LLM configuration:
  - `LLM_BASE_URL`
  - `LLM_TIMEOUT_SECONDS`
  - `LLM_MAX_RETRIES`
  - `AZURE_OPENAI_API_VERSION`
- Added bounded retry handling for transient real-provider failures.
- Added request timeouts around real-provider HTTP calls.
- Added sanitized LLM request logging for provider, model, latency, attempt, and failure reason.
- Preserved prompt secrecy by not logging API keys, authorization headers, or full prompts.
- Added `total_tokens` to `LLMResponse` and stores token usage in RAG audit log metadata when available.
- Added tests for real provider adapters using fake HTTP clients, so tests require no real API keys.

## Phase 3.5 Files Changed

- `apps/api-gateway/app/core/config.py`
- `apps/api-gateway/app/services/llm.py`
- `apps/api-gateway/app/services/rag.py`
- `apps/api-gateway/app/db/rag.py`
- `tests/test_rag.py`
- `.env.example`
- `infra/docker-compose/docker-compose.yml`
- `README.md`
- `docs/task.md`
- `docs/implementation.md`

## Phase 3.5 Design Decisions

- The mock provider remains selected with `LLM_PROVIDER=mock` and does not require a real API key.
- OpenAI-compatible providers use `POST {LLM_BASE_URL}/chat/completions` with a bearer token.
- Azure OpenAI uses `LLM_BASE_URL` as the Azure resource endpoint and `LLM_MODEL` as the deployment name.
- Real-provider retries are limited to timeout, network, rate-limit, and server-side failure cases.
- Provider logs intentionally include only operational metadata, not secrets or sensitive prompt text.

## Phase 3.5 Validation Commands

Run the app with the mock provider:

```powershell
$env:LLM_PROVIDER="mock"; $env:LLM_API_KEY="local-development-placeholder"; $env:LLM_MODEL="mock-rag-local"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Call `POST /rag/query` with the mock provider:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

Run the app with a real OpenAI-compatible provider configured:

```powershell
$env:LLM_PROVIDER="openai"; $env:LLM_API_KEY="<OPENAI_API_KEY>"; $env:LLM_MODEL="gpt-4o-mini"; $env:LLM_BASE_URL="https://api.openai.com/v1"; $env:LLM_TIMEOUT_SECONDS="20"; $env:LLM_MAX_RETRIES="2"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Run the app with Azure OpenAI configured:

```powershell
$env:LLM_PROVIDER="azure_openai"; $env:LLM_API_KEY="<AZURE_OPENAI_API_KEY>"; $env:LLM_MODEL="<AZURE_DEPLOYMENT_NAME>"; $env:LLM_BASE_URL="https://<RESOURCE_NAME>.openai.azure.com"; $env:AZURE_OPENAI_API_VERSION="2024-02-15-preview"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Call `POST /rag/query` with the real provider:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

Verify audit logs store provider, model, latency, and token usage if available:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT llm_provider, llm_model, prompt_tokens, completion_tokens, latency_ms, metadata->'token_usage' AS token_usage, created_at FROM rag_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

Run tests without real API keys:

```bash
pytest
```

## Phase 3.5 Limitations

- Streaming responses are not implemented.
- Token cost estimation is not implemented.
- Real embedding providers are still deferred; document ingestion and retrieval continue to use the mock embedding provider unless extended later.
- Provider-specific advanced options beyond model, base URL, timeout, retries, and Azure API version are not exposed yet.

## Phase 3 Intentionally Skipped Features

- Portfolio upload
- Portfolio analytics
- Compliance service
- Agent workflows
- Airflow DAGs
- Kubernetes manifests
- Terraform modules
- Frontend
- Fine-tuning
- Real-time market data

## Phase 1 Files Created

- `README.md`
- `.env.example`
- `.gitignore`
- `apps/frontend/README.md`
- `apps/api-gateway/README.md`
- `apps/api-gateway/requirements.txt`
- `apps/api-gateway/Dockerfile`
- `apps/api-gateway/.dockerignore`
- `apps/api-gateway/app/__init__.py`
- `apps/api-gateway/app/main.py`
- `apps/api-gateway/app/api/__init__.py`
- `apps/api-gateway/app/api/routes.py`
- `apps/api-gateway/app/core/__init__.py`
- `apps/api-gateway/app/core/config.py`
- `apps/api-gateway/app/core/exceptions.py`
- `apps/api-gateway/app/core/logging.py`
- `apps/api-gateway/app/services/__init__.py`
- `apps/api-gateway/app/services/health.py`
- `services/ingestion-service/README.md`
- `services/rag-service/README.md`
- `services/portfolio-service/README.md`
- `services/compliance-service/README.md`
- `services/agent-service/README.md`
- `packages/common/README.md`
- `packages/llm-core/README.md`
- `packages/rag-core/README.md`
- `packages/security-core/README.md`
- `packages/financial-core/README.md`
- `infra/docker-compose/docker-compose.yml`
- `infra/kubernetes/README.md`
- `infra/terraform/README.md`
- `pipelines/airflow/README.md`
- `tests/test_api_gateway.py`

## How To Run Phase 1

From the repository root:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

The API Gateway runs at:

```text
http://localhost:8000
```

To run the API Gateway directly without Docker:

```powershell
python -m pip install -r apps/api-gateway/requirements.txt
Copy-Item .env.example .env
cd apps/api-gateway
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## How To Validate Phase 1

Start all services:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Call `/health`:

```powershell
curl.exe http://localhost:8000/health
```

Expected result:

```json
{"status":"ok","service":"api-gateway","environment":"local"}
```

Call `/ready`:

```powershell
curl.exe http://localhost:8000/ready
```

Expected result when PostgreSQL, Redis, and Qdrant are reachable:

```json
{
  "status": "ready",
  "service": "api-gateway",
  "checks": {
    "postgresql": {"status": "ok"},
    "redis": {"status": "ok"},
    "qdrant": {"status": "ok"}
  }
}
```

Confirm PostgreSQL is running:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres pg_isready -U wealthops -d wealthops
```

Confirm Redis is running:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec redis redis-cli ping
```

Confirm Qdrant is running:

```powershell
curl.exe http://localhost:6333/readyz
```

Confirm MinIO is running:

```powershell
curl.exe http://localhost:9000/minio/health/live
```

Open the MinIO Console:

```text
http://localhost:9001
```

Local MinIO credentials:

```text
minioadmin / minioadmin
```

Run tests:

```bash
python -m pip install -r apps/api-gateway/requirements.txt
pytest
```

Validate Docker Compose configuration:

```bash
docker compose -f infra/docker-compose/docker-compose.yml config
```

## How To Validate Phase 2

Start all services:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Create a sample TXT file:

```powershell
New-Item -ItemType Directory -Force samples
Set-Content -Path samples/phase2-sample.txt -Value "WealthOps sample document. Revenue increased while liquidity risk remains monitored."
```

Upload the sample TXT file:

```powershell
curl.exe -X POST http://localhost:8000/documents/upload -H "X-Uploaded-By: analyst-1" -F "file=@samples/phase2-sample.txt;type=text/plain"
```

Upload the sample PDF file:

```powershell
curl.exe -X POST http://localhost:8000/documents/upload -H "X-Uploaded-By: analyst-1" -F "file=@tests/fixtures/sample.pdf;type=application/pdf"
```

Check document metadata in PostgreSQL:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT id, filename, content_type, status, chunk_count, object_key, error_message FROM documents ORDER BY created_at DESC LIMIT 10;"
```

Check raw files in MinIO:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose -f infra/docker-compose/docker-compose.yml exec minio mc ls local/wealthops-documents --recursive
```

Check vectors in Qdrant:

```powershell
curl.exe http://localhost:6333/collections/document_chunks
curl.exe -X POST http://localhost:6333/collections/document_chunks/points/scroll -H "Content-Type: application/json" -d '{"limit":5,"with_payload":true,"with_vector":false}'
```

Check document status:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT id, filename, status, error_message FROM documents ORDER BY updated_at DESC LIMIT 10;"
```

Run tests:

```bash
python -m pip install -r apps/api-gateway/requirements.txt
pytest
```

## Intentionally Not Implemented Yet

The following are intentionally not implemented after Phase 3:

- Portfolio upload APIs
- Portfolio exposure calculations
- Compliance APIs
- PII detection
- Prompt injection detection
- Financial advice classifiers
- Agent workflows
- Airflow DAGs
- Kubernetes manifests
- Terraform modules
- Frontend UI

## 2. Engineering Principles

Follow these principles throughout the project:

1. Build small, testable modules.
2. Keep AI provider logic separate from business logic.
3. Keep retrieval logic separate from generation logic.
4. Keep compliance checks independent from LLM generation.
5. Store audit logs for important actions.
6. Avoid hardcoding secrets.
7. Use typed request and response models.
8. Prefer async APIs for I/O-heavy operations.
9. Write tests for core business logic.
10. Make each phase deployable.

## 3. Package Responsibilities

### packages/common

Shared utilities:

- logging
- config
- exceptions
- response models
- pagination
- datetime helpers

### packages/llm-core

LLM abstraction:

- LLMClient interface
- provider implementations
- token usage tracking
- prompt templates
- mock LLM for testing

### packages/rag-core

RAG logic:

- chunking
- embedding interface
- retriever
- reranker
- context builder
- citation builder

### packages/security-core

Security and compliance:

- RBAC helpers
- JWT helpers
- PII detection
- prompt injection checks
- financial advice checks

### packages/financial-core

Financial domain logic:

- portfolio parser
- exposure calculator
- concentration risk rules
- financial metric extraction

## 4. API Design Rules

Every API endpoint should:

- validate request using Pydantic
- return typed response
- log request id
- handle errors cleanly
- avoid leaking internal stack traces
- write audit log for important user actions

## 5. Database Design Notes

Use PostgreSQL for structured metadata.

Important tables:

- users
- documents
- document_chunks
- ingestion_jobs
- portfolios
- portfolio_holdings
- rag_queries
- compliance_results
- audit_logs

## 6. Document Processing Flow

Flow:

1. User uploads document.
2. API validates file.
3. Raw file is stored in object storage.
4. Document row is created with UPLOADED status.
5. Background job sets status to PROCESSING.
6. Text is extracted.
7. Text is chunked.
8. Embeddings are generated.
9. Vectors are stored in Qdrant.
10. Document status becomes INDEXED.

Failure handling:

- If extraction fails, status becomes FAILED.
- Error reason is saved.
- User can retry ingestion.

## 7. RAG Query Flow

Flow:

1. User submits question.
2. System validates user access.
3. Question is embedded.
4. Relevant chunks are retrieved.
5. Context is built.
6. Prompt is sent to LLM.
7. Answer is generated.
8. Citations are attached.
9. Compliance checks are executed.
10. Audit log is saved.
11. Response is returned.

## 8. Compliance Flow

Compliance checks run after retrieval and generation.

Checks:

- Is the user trying prompt injection?
- Does the answer include citations?
- Does the answer include direct financial advice?
- Does the answer expose PII?
- Does the answer make unsupported claims?

Decision:

- SAFE: return normally
- NEEDS_REVIEW: return with warning
- BLOCKED: do not return generated answer

## 9. Portfolio Flow

Flow:

1. User uploads portfolio CSV.
2. System validates required columns.
3. Holdings are stored.
4. Exposure is calculated.
5. Risk rules are applied.
6. Summary is generated.
7. User can ask questions about portfolio.

Required CSV columns:

- asset_name
- ticker
- sector
- region
- quantity
- market_value

## 10. Testing Strategy

### Unit Tests

Test:

- chunking
- portfolio calculations
- compliance rules
- citation builder
- prompt builder

### Integration Tests

Test:

- document upload to PostgreSQL
- vector insert to Qdrant
- RAG endpoint
- portfolio upload

### End-to-End Tests

Test:

- upload document
- ask question
- receive citation-backed answer
- upload portfolio
- get exposure summary

### Load Tests

Test:

- concurrent RAG queries
- document upload throughput
- vector search latency

## 11. Local Development Commands

Example commands:

```bash
docker compose up --build
pytest
ruff check .
mypy .
```

## 12. Definition of Done

A task is done when:

- Code is implemented.
- Tests pass.
- API contract is documented.
- Logs are meaningful.
- Errors are handled.
- Security implications are considered.
- README or implementation notes are updated.
