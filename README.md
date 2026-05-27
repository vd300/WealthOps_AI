# WealthOps AI

WealthOps AI is a secure, cloud-native AI platform for financial document intelligence, portfolio analysis, and compliance-aware LLM workflows.

This repository currently implements **Phase 1: Foundation**, **Phase 2: Document Ingestion**, **Phase 3: RAG Q&A**, **Phase 3.5: Real LLM Provider Integration**, and **Phase 3.6: Document Discovery and RAG Usability Improvements**.

## Phase 1 Includes

- Monorepo folder structure
- FastAPI API Gateway service
- `GET /health` endpoint
- `GET /ready` endpoint
- Structured JSON logging
- Global exception handling
- Docker Compose for API Gateway, PostgreSQL, Qdrant, Redis, and MinIO
- Pydantic Settings configuration
- Basic connection checks for PostgreSQL, Redis, and Qdrant

## Phase 2 Includes

- `POST /documents/upload`
- PDF, TXT, CSV, and XLSX upload validation
- Configurable upload size limit
- Raw file storage in MinIO
- PostgreSQL metadata tables for `documents`, `document_chunks`, and `ingestion_jobs`
- SQL and Alembic migrations for document ingestion tables
- Text extraction for PDF, TXT, CSV, and XLSX files
- Configurable chunk size and overlap
- Provider-agnostic embedding interface with a deterministic local mock provider
- Qdrant vector indexing with chunk metadata payloads
- Document status tracking: `UPLOADED`, `PROCESSING`, `INDEXED`, `FAILED`

## Phase 3 Includes

- `POST /rag/query`
- Typed RAG query request and response models
- Question embedding through the existing provider-agnostic embedding interface
- Qdrant retrieval from the Phase 2 `document_chunks` collection
- Optional `document_ids` filtering
- Prompt construction that instructs the LLM to answer only from retrieved context
- Provider-agnostic LLM client interface with mock/local provider
- Citation building from retrieved chunk metadata
- Confidence score and retrieved chunk summaries
- Safe insufficient-context response for empty retrieval
- PostgreSQL RAG audit logs

## Phase 3.5 Includes

- Mock LLM provider retained for local development and tests
- OpenAI-compatible provider support with `LLM_PROVIDER=openai`
- Azure OpenAI-compatible provider support with `LLM_PROVIDER=azure_openai`
- LLM config for API key, base URL, model, timeout, max retries, and Azure API version
- Timeout and retry handling around real LLM calls
- Sanitized provider logging for provider, model, latency, and failure reason
- RAG audit log storage for provider, model, latency, and token usage when available

## Phase 3.6 Includes

- `GET /documents`
- `GET /documents/{document_id}`
- Upload responses with top-level `document_id`, `filename`, `status`, and `chunk_count`
- Clear RAG validation messages for invalid, missing, and not-indexed `document_ids`
- Swagger/OpenAPI descriptions and examples showing that APIs use UUIDs while user interfaces can display filenames

## Not Implemented Yet

The following are intentionally not implemented yet:

- Portfolio APIs
- Compliance APIs
- Airflow DAGs
- Kubernetes manifests
- Terraform modules
- Frontend UI

## Requirements

- Docker and Docker Compose
- Python 3.12+ if running the API or tests outside Docker

## Run With Docker Compose

From the repository root:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

The API Gateway will be available at:

```text
http://localhost:8000
```

## Validate Phase 1

Call the health endpoint:

```powershell
curl.exe http://localhost:8000/health
```

Call the readiness endpoint:

```powershell
curl.exe http://localhost:8000/ready
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

MinIO Console is available at:

```text
http://localhost:9001
```

Default local MinIO credentials are:

```text
minioadmin / minioadmin
```

## Validate Phase 2

Start the stack:

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

Upload the sample PDF fixture:

```powershell
curl.exe -X POST http://localhost:8000/documents/upload -H "X-Uploaded-By: analyst-1" -F "file=@tests/fixtures/sample.pdf;type=application/pdf"
```

Check document metadata and status in PostgreSQL:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT id, filename, content_type, status, chunk_count, object_key, error_message FROM documents ORDER BY created_at DESC LIMIT 10;"
```

List uploaded documents through the API:

```powershell
curl.exe http://localhost:8000/documents
```

View one uploaded document by UUID:

```powershell
curl.exe http://localhost:8000/documents/<DOCUMENT_ID>
```

Check ingestion jobs:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT id, document_id, status, error_message, started_at, completed_at FROM ingestion_jobs ORDER BY created_at DESC LIMIT 10;"
```

Check stored chunk metadata in PostgreSQL:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT document_id, chunk_index, page_number, left(content, 80) AS preview FROM document_chunks ORDER BY created_at DESC LIMIT 10;"
```

Check raw files in MinIO:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose -f infra/docker-compose/docker-compose.yml exec minio mc ls local/wealthops-documents --recursive
```

Check the Qdrant collection:

```powershell
curl.exe http://localhost:6333/collections/document_chunks
```

Check vectors and payload metadata in Qdrant:

```powershell
curl.exe -X POST http://localhost:6333/collections/document_chunks/points/scroll -H "Content-Type: application/json" -d '{"limit":5,"with_payload":true,"with_vector":false}'
```

## Validate Phase 3

Start the stack:

```bash
docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Upload a sample document if needed:

```powershell
New-Item -ItemType Directory -Force samples
Set-Content -Path samples/phase2-sample.txt -Value "WealthOps sample document. Revenue increased while liquidity risk remains monitored. Market volatility and redemption pressure are noted as key risks."
curl.exe -X POST http://localhost:8000/documents/upload -H "X-Uploaded-By: analyst-1" -F "file=@samples/phase2-sample.txt;type=text/plain"
```

Check that the document is indexed:

```powershell
curl.exe http://localhost:8000/documents
```

Copy an `id` from `GET /documents` where `status` is `INDEXED` and `chunk_count` is greater than `0`. The API uses UUIDs as stable internal identifiers; a frontend would show filenames such as `phase2-sample.txt` while sending the UUID in API requests.

Call `POST /rag/query`:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

Test `document_id` filtering by copying an indexed document id from `GET /documents`:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"document_ids\":[\"<DOCUMENT_ID>\"],\"top_k\":3}"
```

Test invalid document id behavior with a filename instead of a UUID:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"document_ids\":[\"phase2-sample.txt\"],\"top_k\":3}"
```

Test missing document id behavior with a random UUID filter:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"document_ids\":[\"00000000-0000-0000-0000-000000000000\"],\"top_k\":3}"
```

If a valid UUID exists but the document is still `UPLOADED`, `PROCESSING`, `FAILED`, or has `chunk_count` `0`, `/rag/query` returns a clear not-indexed error. Wait for `GET /documents/{document_id}` to show `INDEXED` with chunks before querying that document.

Queries with no matching retrieved chunks still return an insufficient-context response:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What is the debt maturity schedule?\",\"top_k\":5}"
```

Expected insufficient-context fields:

```json
{
  "answer": "I do not have enough retrieved context to answer this question.",
  "citations": [],
  "confidence_score": 0.0,
  "retrieved_chunks": [],
  "status": "insufficient_context",
  "compliance_status": "NEEDS_REVIEW"
}
```

Check RAG audit logs in PostgreSQL:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT user_id, question, retrieved_chunk_ids, llm_provider, llm_model, latency_ms, response_status, compliance_status, created_at FROM rag_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## Run With Mock LLM Provider

The mock provider is the default local path and does not call any external LLM API:

```powershell
$env:LLM_PROVIDER="mock"; $env:LLM_API_KEY="local-development-placeholder"; $env:LLM_MODEL="mock-rag-local"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Call `POST /rag/query` with the mock provider:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

## Run With A Real LLM Provider

OpenAI-compatible provider:

```powershell
$env:LLM_PROVIDER="openai"; $env:LLM_API_KEY="<OPENAI_API_KEY>"; $env:LLM_MODEL="gpt-4o-mini"; $env:LLM_BASE_URL="https://api.openai.com/v1"; $env:LLM_TIMEOUT_SECONDS="20"; $env:LLM_MAX_RETRIES="2"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Azure OpenAI-compatible provider:

```powershell
$env:LLM_PROVIDER="azure_openai"; $env:LLM_API_KEY="<AZURE_OPENAI_API_KEY>"; $env:LLM_MODEL="<AZURE_DEPLOYMENT_NAME>"; $env:LLM_BASE_URL="https://<RESOURCE_NAME>.openai.azure.com"; $env:AZURE_OPENAI_API_VERSION="2024-02-15-preview"; docker compose -f infra/docker-compose/docker-compose.yml up --build
```

Call `POST /rag/query` with the real provider:

```powershell
curl.exe -X POST http://localhost:8000/rag/query -H "Content-Type: application/json" -H "X-User-ID: analyst-1" -d "{\"question\":\"What risks are mentioned?\",\"top_k\":5}"
```

Verify RAG audit log provider, model, latency, and token usage:

```bash
docker compose -f infra/docker-compose/docker-compose.yml exec postgres psql -U wealthops -d wealthops -c "SELECT llm_provider, llm_model, prompt_tokens, completion_tokens, latency_ms, metadata->'token_usage' AS token_usage, created_at FROM rag_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## Run API Gateway Locally Without Docker

Install dependencies:

```bash
python -m pip install -r apps/api-gateway/requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Start the API:

```bash
cd apps/api-gateway
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run Tests

After installing API Gateway dependencies:

```bash
pytest
```
