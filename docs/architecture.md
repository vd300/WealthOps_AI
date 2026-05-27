# WealthOps AI — Architecture

## 1. Architecture Overview

WealthOps AI uses a cloud-native, service-oriented architecture.

The main idea is simple:

- Store financial documents.
- Convert documents into searchable chunks.
- Use embeddings and vector search to retrieve relevant context.
- Use an LLM to answer questions.
- Use compliance guardrails to reduce risk.
- Use audit logs and monitoring to make the system production-ready.

## 2. High-level Architecture

```text
Frontend
   |
API Gateway
   |
   |--------------------------
   |            |            |
Ingestion    RAG        Portfolio
Service      Service    Service
   |            |            |
   |            |            |
Object       Qdrant     PostgreSQL
Storage      Vector DB  Metadata DB
   |
Airflow Pipelines

Compliance Service is used by API Gateway, RAG Service, Portfolio Service, and Agent Service.

Observability collects logs, metrics, and traces from all services.
```

## 3. Component Responsibilities

### Frontend

The frontend provides:

- login page
- document upload UI
- document list
- chat/Q&A interface
- portfolio upload UI
- portfolio dashboard
- compliance warning display

### API Gateway

The API Gateway is the main entry point.

Responsibilities:

- authenticate requests
- validate roles
- route requests
- apply rate limits
- write audit logs
- expose public APIs

### Ingestion Service

The Ingestion Service handles document processing.

Responsibilities:

- validate uploaded files
- extract text
- split documents into chunks
- generate embeddings
- store vectors
- update ingestion status

### RAG Service

The RAG Service handles question answering.

Responsibilities:

- convert question to embedding
- retrieve chunks
- build prompt
- call LLM
- create citations
- return answer

### Portfolio Service

The Portfolio Service handles structured financial data.

Responsibilities:

- parse portfolio CSV
- calculate exposure
- detect concentration risk
- summarize portfolio

### Compliance Service

The Compliance Service validates user input and LLM output.

Responsibilities:

- detect prompt injection
- detect PII
- detect financial advice risk
- check citation coverage
- classify response risk

### Agent Service

The Agent Service performs multi-step workflows.

Responsibilities:

- orchestrate tools
- search documents
- extract financial risks
- compare metrics
- generate structured reports
- call compliance checks

### Airflow

Airflow runs scheduled jobs.

Responsibilities:

- daily document ingestion
- daily portfolio risk scans
- weekly embedding refresh
- RAG quality evaluation

### Observability Stack

Observability includes:

- Prometheus
- Grafana
- OpenTelemetry
- structured JSON logs

## 4. Data Flow: Document Upload

```text
User uploads document
        |
API Gateway validates request
        |
Ingestion Service stores raw file
        |
PostgreSQL stores metadata
        |
Text extraction runs
        |
Document is chunked
        |
Embeddings are generated
        |
Qdrant stores vectors
        |
Document status becomes INDEXED
```

## 5. Data Flow: RAG Query

```text
User asks question
        |
API Gateway validates user
        |
RAG Service embeds question
        |
Qdrant retrieves relevant chunks
        |
Prompt builder creates context
        |
LLM generates answer
        |
Citation builder attaches sources
        |
Compliance Service validates answer
        |
Audit log is stored
        |
Answer is returned
```

## 6. Data Flow: Portfolio Analysis

```text
User uploads portfolio CSV
        |
Portfolio Service validates file
        |
Holdings are stored
        |
Exposure is calculated
        |
Risk rules are applied
        |
Summary is generated
        |
User views portfolio dashboard
```

## 7. Scalability Design

The system scales through:

- stateless API services
- horizontal scaling on Kubernetes
- separate vector database
- async background processing
- Airflow for batch work
- Redis caching
- object storage for large files

## 8. Reliability Design

Reliability is improved using:

- health checks
- readiness checks
- retries
- idempotent ingestion
- document processing status
- failed job tracking
- graceful fallback if LLM fails

## 9. Security Design

Security includes:

- JWT authentication
- RBAC
- file validation
- PII detection
- prompt injection detection
- audit logs
- secret management
- encryption in transit
- encryption at rest in cloud

## 10. Performance Design

Performance improvements include:

- async FastAPI endpoints
- Redis caching
- top-k vector retrieval
- DB indexes
- pagination
- request timeouts
- load testing
- streaming responses later

## 11. Why This Architecture Is Interview Strong

This architecture is strong because it is not only an AI demo.

It shows:

- real system design
- production thinking
- regulated environment awareness
- separation of concerns
- scalable ML workflow
- cloud-native deployment
- monitoring and debugging
- secure AI design