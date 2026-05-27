# WealthOps AI — Product Requirements Document

## 1. Product Summary

WealthOps AI is a secure, cloud-native AI platform for financial document intelligence, portfolio analysis, and compliance-aware LLM workflows.

The platform helps asset and wealth management teams upload financial documents, ask questions, summarize information, analyze portfolio exposure, and detect compliance risks using Retrieval-Augmented Generation, vector search, agentic workflows, and audit logging.

## 2. Problem

Asset and Wealth Management teams deal with large amounts of unstructured and semi-structured financial data.

Examples include:

- Annual reports
- Fund factsheets
- Earnings transcripts
- Analyst notes
- Research PDFs
- Portfolio CSV files
- Risk disclosures
- Internal investment documents

The main problems are:

- Financial documents are large and hard to search manually.
- Analysts spend too much time reading repetitive documents.
- Important risks may be missed.
- AI answers can hallucinate if not grounded in documents.
- Financial institutions require strong auditability and compliance controls.
- Portfolio exposure analysis often requires manual spreadsheet work.

## 3. Product Goals

The product should:

1. Allow users to upload financial documents.
2. Extract and index document content.
3. Support semantic search and RAG-based Q&A.
4. Return answers with citations.
5. Analyze portfolio holdings.
6. Detect concentration and risk exposure.
7. Use compliance guardrails before returning LLM outputs.
8. Track audit logs for regulated environments.
9. Expose production metrics for monitoring.
10. Be deployable using Docker, Kubernetes, and Terraform.

## 4. Target Users

### Primary Users

- Wealth advisors
- Financial analysts
- Portfolio managers
- Investment research teams

### Secondary Users

- Compliance reviewers
- Data science teams
- DevOps teams
- Cybersecurity teams

## 5. Core User Stories

### Document Upload

As a financial analyst, I want to upload annual reports and research PDFs so that I can search and analyze them later.

### Document Q&A

As an analyst, I want to ask questions about uploaded documents so that I can quickly find relevant information.

### Citation-backed Answers

As a compliance-aware user, I want AI answers to include source citations so that I can verify where the answer came from.

### Portfolio Upload

As a portfolio manager, I want to upload a portfolio CSV so that I can understand exposure by sector, region, and asset.

### Risk Detection

As a wealth advisor, I want the system to detect portfolio concentration risks so that I can review risky positions.

### Compliance Review

As a compliance user, I want AI responses to be checked for unsupported financial advice, missing citations, and PII leakage.

### Audit Trail

As an administrator, I want every user action and AI response to be logged so that activity can be reviewed later.

## 6. Functional Requirements

### FR1: Authentication and Authorization

The system shall support:

- User login
- JWT-based authentication
- Role-based access control
- Admin, analyst, advisor, and compliance roles

### FR2: Document Upload

The system shall support:

- PDF upload
- CSV upload
- Excel upload
- File validation
- File metadata extraction
- Secure storage of raw files

### FR3: Document Processing

The system shall:

- Extract text from documents
- Clean extracted text
- Split text into chunks
- Generate embeddings
- Store embeddings in a vector database
- Track document processing status

Document statuses:

- UPLOADED
- PROCESSING
- INDEXED
- FAILED

### FR4: RAG Question Answering

The system shall:

- Accept user questions
- Retrieve relevant chunks from vector database
- Build context
- Generate LLM response
- Attach citations
- Return confidence score
- Store the full interaction in audit logs

### FR5: Portfolio Analysis

The system shall:

- Accept portfolio CSV files
- Parse holdings
- Calculate sector exposure
- Calculate region exposure
- Calculate asset allocation
- Detect top holdings
- Detect concentration risks
- Generate portfolio summary

### FR6: Compliance Guardrails

The system shall check:

- Missing citations
- Unsupported investment claims
- Direct financial advice
- PII exposure
- Prompt injection attempts
- Confidential data leakage

Compliance statuses:

- SAFE
- NEEDS_REVIEW
- BLOCKED

### FR7: Agentic Research Workflow

The system shall support a research agent that can:

- Search documents
- Extract risks
- Extract financial metrics
- Compare documents
- Generate summaries
- Run compliance checks

### FR8: Batch Pipelines

The system shall use Airflow for:

- Daily document ingestion
- Daily portfolio risk scans
- Weekly embedding refresh
- RAG quality evaluation

### FR9: Observability

The system shall expose:

- API latency metrics
- Error rate
- LLM token usage
- LLM cost estimate
- Retrieval latency
- Compliance block count
- Document processing failures

## 7. Non-functional Requirements

### Security

- Authentication required for protected APIs
- Role-based access control
- Secrets must not be hardcoded
- Audit logs must be stored
- Sensitive data should be masked where needed

### Scalability

- Services should be stateless where possible
- APIs should support horizontal scaling
- Long-running jobs should run asynchronously
- Vector search should be separated from metadata storage

### Reliability

- Failed jobs should be retryable
- Document status should be visible
- Ingestion should be idempotent
- Health checks should be available

### Performance

- RAG queries should use top-k retrieval
- Frequent queries may be cached
- Upload processing should be asynchronous
- APIs should support pagination

### Compliance

- AI answers should be citation-backed
- Risky responses should be flagged
- All user actions should be auditable

## 8. MVP Scope

The MVP includes:

1. User authentication
2. Document upload
3. Text extraction
4. Chunking
5. Embedding generation
6. Qdrant vector search
7. RAG Q&A with citations
8. Portfolio CSV upload
9. Basic portfolio exposure summary
10. Compliance warning layer
11. Audit logging
12. Docker Compose setup

## 9. Out of Scope for MVP

The following are not part of the first MVP:

- Real trading recommendations
- Real client data
- Production-grade fine-tuning
- Full enterprise identity integration
- Complex regulatory approval workflows
- Real-time market data feeds
- Multi-region deployment

## 10. Success Metrics

The MVP is successful when:

- Users can upload a document.
- The system indexes it successfully.
- Users can ask questions and get citation-backed answers.
- Portfolio CSV files can be uploaded and summarized.
- Compliance warnings are generated for risky outputs.
- APIs are tested.
- The app can run locally using Docker Compose.
- Basic Kubernetes manifests are available.