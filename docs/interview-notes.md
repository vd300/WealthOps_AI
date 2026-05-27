# WealthOps AI — Interview Notes

## 1. Simple Project Explanation

WealthOps AI is a secure AI platform for financial document intelligence and portfolio analysis.

It allows users to upload financial documents and portfolio files, ask questions, get citation-backed answers, analyze portfolio exposure, and detect compliance risks.

## 2. 30-second Pitch

"I built a cloud-native AI platform for Asset and Wealth Management use cases. The system ingests financial documents, creates embeddings, stores them in a vector database, and uses RAG to answer questions with citations. It also supports portfolio exposure analysis, compliance guardrails, audit logging, Airflow batch pipelines, Kubernetes deployment, Terraform infrastructure, and Prometheus/Grafana observability."

## 3. 2-minute Pitch

"The project is called WealthOps AI. It is designed for financial analysts and wealth advisors who need to work with large financial documents and portfolio data. Users can upload annual reports, fund factsheets, research notes, and portfolio CSVs. The ingestion service extracts text, chunks it, creates embeddings, and stores them in Qdrant. When a user asks a question, the RAG service retrieves relevant chunks, builds a context-aware prompt, calls the LLM, and returns an answer with citations.

Since this is a financial services use case, I added a compliance layer that checks for missing citations, prompt injection, PII exposure, unsupported claims, and direct financial advice. I also added audit logging so every important user action and AI response can be reviewed later.

From an engineering side, the project uses FastAPI, PostgreSQL, Redis, Qdrant, Airflow, Docker, Kubernetes, Terraform, Prometheus, and Grafana. The system is designed as modular services so it can scale horizontally and be deployed in a cloud-native way."

## 4. How It Maps to JPMorgan Role

### LLM-driven applications

The project uses RAG, embeddings, prompt templates, LLM generation, and agentic workflows.

### Scalable ML-driven products

The system separates ingestion, retrieval, generation, compliance, and monitoring.

### Data Science collaboration

The project includes embeddings, retrieval quality metrics, prompt evaluation, and RAG quality scoring.

### Cybersecurity collaboration

The project includes RBAC, PII detection, prompt injection detection, secrets management, and audit logs.

### DevOps collaboration

The project includes Docker, Kubernetes, Terraform, CI/CD, Airflow, Prometheus, and Grafana.

### Regulated environment

The project includes citation-backed answers, compliance statuses, audit trails, and restricted financial advice handling.

### Performance tuning

The project includes async APIs, Redis caching, vector search optimization, DB indexing, p95 latency tracking, and load testing.

## 5. Important Technical Decisions

### Why FastAPI?

FastAPI is suitable because it supports async APIs, Pydantic validation, automatic OpenAPI docs, and high-performance Python services.

### Why Qdrant?

Qdrant is used for vector search. It stores document chunk embeddings and supports semantic retrieval for RAG.

### Why PostgreSQL?

PostgreSQL stores structured metadata such as users, documents, portfolios, audit logs, and compliance results.

### Why Redis?

Redis is used for caching, rate limiting, and temporary job state.

### Why Airflow?

Airflow is used for scheduled and repeatable data workflows such as daily ingestion, portfolio risk scans, and embedding refresh.

### Why Kubernetes?

Kubernetes allows the services to be deployed, scaled, monitored, and restarted independently.

### Why Terraform?

Terraform makes infrastructure reproducible. It can provision storage, database, Kubernetes cluster, container registry, and secrets.

## 6. Memory Hook

Remember the project with this sentence:

"Upload financial data, understand it with RAG, protect it with compliance, operate it with cloud-native infrastructure."

Or shorter:

"Upload. Search. Answer. Analyze. Guard. Audit. Deploy. Monitor."

## 7. Architecture Memory Trick

Use this order:

1. User uploads document.
2. Ingestion extracts text.
3. Text becomes chunks.
4. Chunks become embeddings.
5. Embeddings go to Qdrant.
6. Question comes in.
7. Retriever finds chunks.
8. LLM answers with citations.
9. Compliance checks answer.
10. Audit log stores everything.

## 8. STAR Answer Example

### Situation

Financial analysts need to review large documents and portfolio data, but manual review is slow and difficult to audit.

### Task

I wanted to build a production-style AI platform that could answer questions from financial documents while remaining secure and compliant.

### Action

I designed a modular architecture using FastAPI, PostgreSQL, Qdrant, Redis, Airflow, Kubernetes, and Terraform. I implemented a RAG pipeline for citation-backed answers, a portfolio analysis module, compliance guardrails, audit logging, and observability with Prometheus and Grafana.

### Result

The project demonstrates how to build and operate a scalable LLM-driven financial application in a regulated environment.

## 9. Questions Interviewer May Ask

### How do you prevent hallucination?

Answer:

"I do not allow the model to answer freely for document-specific questions. The RAG service retrieves relevant chunks, builds a grounded prompt, requires citations, and flags answers without source support. If retrieval returns weak context, the system should say it does not have enough information."

### How do you handle prompt injection?

Answer:

"I treat uploaded document text as untrusted input. The system scans for suspicious instructions, separates system instructions from retrieved context, and runs compliance checks before returning the final answer."

### How do you scale document processing?

Answer:

"Document upload is separated from document processing. The API stores the file and metadata quickly, then background workers or Airflow process extraction, chunking, embeddings, and indexing. This allows the API to remain responsive while processing scales independently."

### How do you monitor the LLM system?

Answer:

"I track API latency, retrieval latency, LLM latency, token usage, estimated cost, citation coverage, compliance warnings, and failed ingestion jobs. These metrics are exposed to Prometheus and visualized in Grafana."

### How do you make it cloud-native?

Answer:

"Each service is containerized, deployed on Kubernetes, configured using ConfigMaps and Secrets, and provisioned through Terraform. Services are stateless where possible and can scale horizontally."

### How do you support regulated financial use cases?

Answer:

"I added RBAC, audit logging, citation-backed answers, PII checks, financial advice detection, and compliance statuses like SAFE, NEEDS_REVIEW, and BLOCKED."

## 10. Final Interview Pitch

"My project is not just a PDF chatbot. It is a regulated financial AI platform. I focused on the full software engineering lifecycle: architecture, secure APIs, RAG, compliance, batch pipelines, deployment, observability, testing, and performance. That aligns closely with the responsibilities of a Software Engineer III role in Asset and Wealth Management."