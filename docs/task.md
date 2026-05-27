# WealthOps AI — Task Breakdown

## Phase 1: Foundation

### Task 1.1: Create Monorepo Structure

Create folders:

- apps/frontend
- apps/api-gateway
- services/ingestion-service
- services/rag-service
- services/portfolio-service
- services/compliance-service
- services/agent-service
- packages/common
- packages/llm-core
- packages/rag-core
- packages/security-core
- packages/financial-core
- infra/docker-compose
- infra/kubernetes
- infra/terraform
- pipelines/airflow
- tests

Acceptance criteria:

- Folder structure exists.
- README.md explains the project.
- Each service has its own README.md.

### Task 1.2: Create FastAPI API Gateway

Build:

- FastAPI app
- health endpoint
- readiness endpoint
- structured logging
- exception handler

Endpoints:

- GET /health
- GET /ready

Acceptance criteria:

- App runs locally.
- Health endpoint returns OK.
- Logs are JSON-formatted.

### Task 1.3: Add Docker Compose

Add services:

- api-gateway
- PostgreSQL
- Qdrant
- Redis
- MinIO

Acceptance criteria:

- docker compose up starts all services.
- API can connect to PostgreSQL, Redis, and Qdrant.

### Task 1.4: Add Configuration Management

Use Pydantic settings.

Required config:

- DATABASE_URL
- REDIS_URL
- QDRANT_URL
- OBJECT_STORAGE_URL
- JWT_SECRET
- LLM_PROVIDER
- LLM_API_KEY

Acceptance criteria:

- Config is loaded from environment variables.
- Missing required config fails safely.

## Phase 2: Document Ingestion

### Task 2.1: Create Document Metadata Model

Create tables:

- documents
- document_chunks
- ingestion_jobs

Document fields:

- id
- filename
- content_type
- status
- uploaded_by
- created_at
- updated_at

Acceptance criteria:

- Alembic migration exists.
- Tables are created in PostgreSQL.

### Task 2.2: Build File Upload API

Endpoint:

- POST /documents/upload

Acceptance criteria:

- Accepts PDF, CSV, XLSX, TXT.
- Rejects unsupported file types.
- Enforces file size limit.
- Stores metadata in PostgreSQL.
- Stores raw file in object storage.

### Task 2.3: Implement Text Extraction

Support:

- PDF text extraction
- TXT extraction
- CSV parsing
- XLSX parsing

Acceptance criteria:

- Extracted text is saved.
- Failed extraction updates status to FAILED.

### Task 2.4: Implement Chunking

Create chunking logic:

- configurable chunk size
- configurable overlap
- page number tracking
- chunk metadata

Acceptance criteria:

- Document text is split into chunks.
- Chunks preserve document id and page reference.

### Task 2.5: Generate Embeddings and Store in Qdrant

Acceptance criteria:

- Each chunk gets an embedding.
- Embeddings are stored in Qdrant.
- Chunk metadata is stored with vector.

## Phase 3: RAG Q&A

### [x] Task 3.1: Create RAG Query Endpoint

Endpoint:

- POST /rag/query

Request:

```json
{
  "question": "What are the key risks?",
  "document_ids": ["doc_123"],
  "top_k": 5
}
```

Acceptance criteria:

- Validates request.
- Returns answer, citations, confidence, compliance status.

### [x] Task 3.2: Implement Retriever

Acceptance criteria:

- Converts question to embedding.
- Searches Qdrant.
- Filters by document ids.
- Returns top-k chunks.

### [x] Task 3.3: Implement Prompt Builder

Acceptance criteria:

- Builds prompt using retrieved chunks.
- Instructs model to answer only from context.
- Requires citations.
- Handles empty retrieval safely.

### [x] Task 3.4: Implement LLM Client

Acceptance criteria:

- Provider-agnostic interface exists.
- Supports mock provider for tests.
- Supports real provider through config.

### [x] Task 3.5: Implement Citation Builder

Acceptance criteria:

- Response includes source document id.
- Response includes chunk id.
- Response includes page number if available.

### [x] Task 3.6: Add RAG Audit Logging

Acceptance criteria:

- Stores user question.
- Stores retrieved chunk ids.
- Stores model name.
- Stores token usage if available.
- Stores compliance result.

### [x] Phase 3.5: Real LLM Provider Integration

Acceptance criteria:

- Keeps the mock LLM provider for tests and local development.
- Uses the provider-agnostic `LLMClient` interface for mock and real providers.
- Supports `LLM_PROVIDER=mock`, `LLM_PROVIDER=openai`, and `LLM_PROVIDER=azure_openai`.
- Adds configuration for API key, base URL, model name, timeout, max retries, and Azure API version.
- Applies timeout and bounded retry handling around real LLM calls.
- Logs provider, model, latency, and sanitized failure reason without logging secrets or full prompts.
- Stores provider, model, latency, and available token usage in RAG audit logs.
- Keeps tests independent of real LLM API keys.

### [x] Phase 3.6: Document Discovery and RAG Usability Improvements

Acceptance criteria:

- Adds `GET /documents` for uploaded document discovery.
- Adds `GET /documents/{document_id}` for document details.
- Upload response clearly returns `document_id`, `filename`, `status`, and `chunk_count`.
- RAG validation clearly explains invalid, missing, and not-indexed `document_ids`.
- README explains uploading, listing documents, copying `document_id`, and using it in `POST /rag/query`.
- Swagger/OpenAPI examples use realistic UUIDs and explain that frontends can show filenames while APIs use UUIDs.
- UUIDs remain the primary API identifiers; filenames are not used as primary identifiers.

## Phase 4: Portfolio Intelligence

### [ ] Task 4.1: Portfolio Upload API

Endpoint:

- POST /portfolios/upload

Acceptance criteria:

- Accepts CSV.
- Validates required columns.
- Stores portfolio metadata.
- Stores holdings.

### [ ] Task 4.2: Exposure Calculation

Calculate:

- sector exposure
- region exposure
- asset exposure
- top holdings
- concentration percentage

Acceptance criteria:

- Portfolio summary endpoint returns calculated exposure.

### [ ] Task 4.3: Concentration Risk Rules

Rules:

- Single holding > 20% = high concentration risk
- Sector exposure > 40% = sector concentration risk
- Region exposure > 50% = regional concentration risk

Acceptance criteria:

- Risk alerts are generated.

### [ ] Task 4.4: Portfolio Q&A

Endpoint:

- POST /portfolios/{portfolio_id}/ask

Acceptance criteria:

- User can ask questions about portfolio.
- Uses calculated metrics as context.
- Returns answer and risk warnings.

## Phase 5: Compliance Guardrails

### [ ] Task 5.1: PII Detection

Detect:

- email
- phone number
- PAN-like identifiers
- account numbers
- client identifiers

Acceptance criteria:

- Sensitive values are flagged or masked.

### [ ] Task 5.2: Prompt Injection Detection

Detect suspicious instructions like:

- ignore previous instructions
- reveal system prompt
- bypass policy
- print hidden context

Acceptance criteria:

- Suspicious input is blocked or flagged.

### [ ] Task 5.3: Citation Coverage Checker

Acceptance criteria:

- Answers without citations are flagged.
- Claims not supported by context are marked NEEDS_REVIEW.

### [ ] Task 5.4: Financial Advice Risk Classifier

Detect phrases like:

- buy this stock
- sell this holding
- guaranteed return
- risk-free investment

Acceptance criteria:

- Risky answer is marked NEEDS_REVIEW or BLOCKED.

## Phase 6: Agentic Research Workflow

### [ ] Task 6.1: Define Agent Tool Interface

Tools:

- search_documents
- extract_risks
- extract_metrics
- compare_periods
- check_compliance
- generate_summary

Acceptance criteria:

- Each tool has typed input and output.

### [ ] Task 6.2: Implement Research Analysis Agent

Endpoint:

- POST /agents/research-analysis

Acceptance criteria:

- Agent performs multi-step workflow.
- Returns structured research summary.
- Includes citations.
- Runs compliance check.

## Phase 7: Airflow Pipelines

### [ ] Task 7.1: Daily Document Ingestion DAG

Acceptance criteria:

- Scans object storage for new docs.
- Processes unindexed docs.
- Updates statuses.

### [ ] Task 7.2: Daily Portfolio Risk Scan DAG

Acceptance criteria:

- Finds active portfolios.
- Recalculates exposure.
- Generates risk alerts.

### [ ] Task 7.3: Weekly Embedding Refresh DAG

Acceptance criteria:

- Finds stale embeddings.
- Recomputes embeddings.
- Updates Qdrant.

### [ ] Task 7.4: RAG Evaluation DAG

Acceptance criteria:

- Runs predefined questions.
- Measures answer quality.
- Tracks citation coverage.

## Phase 8: Deployment

### [ ] Task 8.1: Dockerfiles

Acceptance criteria:

- Each service has Dockerfile.
- Images build successfully.

### [ ] Task 8.2: Kubernetes Manifests

Create:

- Deployment
- Service
- ConfigMap
- Secret
- Ingress
- HPA

Acceptance criteria:

- Services deploy to local Kubernetes.

### [ ] Task 8.3: Terraform

Provision:

- Kubernetes cluster
- database
- object storage
- container registry
- secrets

Acceptance criteria:

- Terraform plan works.
- Infra modules are reusable.

## Phase 9: Observability and Performance

### [ ] Task 9.1: Prometheus Metrics

Track:

- request count
- latency
- error count
- LLM token usage
- retrieval latency
- compliance block count

Acceptance criteria:

- /metrics endpoint exists.
- Prometheus can scrape it.

### [ ] Task 9.2: Grafana Dashboards

Dashboards:

- API health
- RAG performance
- LLM cost
- ingestion jobs
- compliance alerts

Acceptance criteria:

- Dashboard JSON files exist.

### [ ] Task 9.3: Load Testing

Use Locust or k6.

Acceptance criteria:

- Test RAG endpoint.
- Report p95 latency.
- Identify bottlenecks.

### [ ] Task 9.4: Performance Optimization

Add:

- Redis caching
- DB indexes
- async LLM calls
- pagination
- request timeouts

Acceptance criteria:

- p95 latency improves after optimization.

## Backlog

- Add real LLM provider adapters for Azure OpenAI, OpenAI, AWS Bedrock, or local model servers.
- Add request-time access checks before allowing users to filter/query restricted documents.
- Add stronger citation coverage and unsupported-claim validation when Phase 5 compliance is implemented.
- Add retrieval evaluation datasets and scheduled RAG quality jobs when Phase 7 is implemented.
