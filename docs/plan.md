# WealthOps AI — Technical Plan

## 1. Project Objective

Build a production-style AI platform that demonstrates the skills needed for a Software Engineer III role in Asset & Wealth Management.

The project should show ability in:

- Advanced Python
- FastAPI
- LLM applications
- RAG
- Agentic AI workflows
- Financial data processing
- Secure software design
- Kubernetes
- Airflow
- Terraform
- Observability
- Performance optimization

## 2. Architecture Style

Use a modular microservice-style architecture.

For development simplicity, services can initially live in one monorepo and run through Docker Compose. Later, they can be deployed independently on Kubernetes.

## 3. Main Components

### API Gateway

Responsibilities:

- Authentication
- Authorization
- Request validation
- Routing
- Audit logging
- Rate limiting

### Ingestion Service

Responsibilities:

- File upload handling
- Text extraction
- Metadata extraction
- Chunking
- Embedding generation
- Vector indexing

### RAG Service

Responsibilities:

- Query rewriting
- Vector search
- Context building
- LLM response generation
- Citation creation
- Confidence scoring

### Portfolio Service

Responsibilities:

- Portfolio CSV parsing
- Exposure calculation
- Concentration risk detection
- Portfolio summary generation

### Compliance Service

Responsibilities:

- Prompt injection detection
- PII checks
- Unsupported claim detection
- Citation coverage validation
- Financial advice risk classification

### Agent Service

Responsibilities:

- Multi-step research workflows
- Tool orchestration
- Risk extraction
- Report generation

### Airflow Pipelines

Responsibilities:

- Scheduled ingestion
- Embedding refresh
- Portfolio risk scans
- RAG evaluation jobs

### Observability

Responsibilities:

- Metrics
- Logs
- Traces
- LLM cost tracking
- Dashboarding

## 4. Data Stores

### PostgreSQL

Used for:

- Users
- Documents
- Document metadata
- Portfolio metadata
- Audit logs
- Compliance results

### Qdrant

Used for:

- Vector embeddings
- Semantic search
- Chunk similarity lookup

### Redis

Used for:

- Caching
- Rate limiting
- Temporary job state

### Object Storage

Used for:

- Raw uploaded files
- Extracted text artifacts
- Generated reports

Local development can use MinIO as an S3-compatible object store.

## 5. LLM Provider Design

The system should not be tightly coupled to one LLM provider.

Create a provider abstraction:

```python
class LLMClient:
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        ...
```

Supported providers can include:

- Azure OpenAI
- OpenAI
- AWS Bedrock
- Local model later

## 6. RAG Pipeline

The RAG pipeline has these steps:

1. Receive user question.
2. Validate request.
3. Rewrite question if needed.
4. Generate query embedding.
5. Search Qdrant for top-k chunks.
6. Apply optional reranking.
7. Build prompt with retrieved context.
8. Call LLM.
9. Generate answer.
10. Add citations.
11. Run compliance validation.
12. Save audit log.
13. Return response.

## 7. Agent Workflow

The AI Research Analyst Agent performs multi-step analysis.

Example workflow:

1. Understand user request.
2. Select tools.
3. Search relevant documents.
4. Extract financial risks.
5. Extract financial metrics.
6. Compare periods.
7. Generate summary.
8. Run compliance check.
9. Return citation-backed report.

## 8. Security Plan

Security should include:

- JWT authentication
- RBAC
- Input validation
- File type validation
- File size limits
- Secrets through environment variables
- Audit logging
- PII masking
- Prompt injection detection
- HTTPS in cloud deployment

## 9. Deployment Plan

### Local Development

Use Docker Compose for:

- API services
- PostgreSQL
- Qdrant
- Redis
- MinIO
- Airflow
- Prometheus
- Grafana

### Kubernetes

Use Kubernetes for:

- Deployments
- Services
- ConfigMaps
- Secrets
- Horizontal Pod Autoscaler
- Ingress
- Health checks

### Terraform

Use Terraform for provisioning:

- Kubernetes cluster
- Object storage
- Database
- Container registry
- Networking
- IAM roles
- Secrets manager

## 10. Development Phases

### Phase 1: Foundation

- Monorepo setup
- FastAPI app
- Docker Compose
- PostgreSQL
- Qdrant
- Redis
- Health checks
- Logging

### Phase 2: Document Ingestion

- Upload endpoint
- File validation
- Text extraction
- Chunking
- Embedding generation
- Vector indexing

### Phase 3: RAG Q&A

- Query endpoint
- Vector search
- Prompt template
- LLM client
- Citations
- Audit log

### Phase 4: Portfolio Intelligence

- Portfolio upload
- Exposure calculation
- Risk detection
- Portfolio summary API

### Phase 5: Compliance

- PII detector
- Prompt injection detector
- Citation checker
- Financial advice classifier

### Phase 6: Agentic Workflow

- Research agent
- Tool interface
- Multi-step analysis
- Compliance-integrated final answer

### Phase 7: Airflow

- Daily ingestion DAG
- Portfolio risk scan DAG
- Embedding refresh DAG
- RAG evaluation DAG

### Phase 8: Kubernetes and Terraform

- Dockerfiles
- Kubernetes manifests
- Helm chart
- Terraform modules
- CI/CD deployment pipeline

### Phase 9: Observability and Performance

- Prometheus metrics
- Grafana dashboards
- OpenTelemetry tracing
- Load testing
- Caching
- Performance tuning

## 11. Interview Strategy

When explaining the project, do not say:

"I built a chatbot over PDFs."

Say:

"I built a secure, cloud-native AI platform for financial document intelligence and portfolio analysis. It uses RAG, vector search, compliance guardrails, audit logs, Airflow pipelines, Kubernetes deployment, and observability to support regulated asset and wealth management workflows."