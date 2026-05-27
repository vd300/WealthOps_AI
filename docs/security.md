# WealthOps AI — Security and Compliance Plan

## 1. Security Objective

The project is designed for a regulated financial environment. The system should protect user data, prevent unsafe AI behavior, and maintain auditability.

## 2. Security Requirements

The system should support:

- authentication
- authorization
- secure file upload
- input validation
- prompt injection detection
- PII detection
- audit logging
- secrets management
- compliance classification
- safe LLM response handling

## 3. Authentication

Use JWT-based authentication for MVP.

Flow:

1. User logs in.
2. System validates credentials.
3. System issues access token.
4. User sends token with requests.
5. API validates token before processing request.

## 4. Authorization

Use role-based access control.

Roles:

- ADMIN
- ANALYST
- ADVISOR
- COMPLIANCE_REVIEWER

Example permissions:

| Action | ADMIN | ANALYST | ADVISOR | COMPLIANCE |
|---|---|---|---|---|
| Upload documents | Yes | Yes | Yes | No |
| Ask RAG questions | Yes | Yes | Yes | Yes |
| Upload portfolio | Yes | Yes | Yes | No |
| View audit logs | Yes | No | No | Yes |
| Review compliance alerts | Yes | No | No | Yes |

## 5. File Upload Security

File upload risks:

- malicious files
- huge files
- unsupported formats
- hidden scripts
- sensitive data exposure

Controls:

- allow only supported extensions
- enforce file size limit
- validate MIME type
- store files outside web root
- scan file metadata
- never execute uploaded files
- log upload events

## 6. Prompt Injection Protection

Prompt injection means the user or document tries to override system instructions.

Examples:

- ignore previous instructions
- reveal system prompt
- bypass compliance
- output hidden context
- do not cite sources

Controls:

- detect suspicious phrases
- separate system instructions from document context
- instruct model not to follow document instructions
- run compliance check before response
- block or flag suspicious queries

## 7. PII Detection

Detect sensitive data such as:

- email addresses
- phone numbers
- account numbers
- client identifiers
- PAN-like patterns
- addresses

For MVP, use regex-based detection.

Later, use:

- named entity recognition
- cloud DLP tools
- ML-based sensitive data detection

## 8. Financial Advice Guardrail

The system should avoid producing direct investment advice.

Risky phrases:

- buy this stock
- sell this asset
- guaranteed return
- risk-free investment
- you should invest in
- this will definitely increase

Allowed behavior:

- summarize document content
- explain risks
- describe exposure
- compare available data
- say when information is insufficient

Unsafe behavior:

- giving personalized financial advice
- guaranteeing returns
- recommending trades without review
- making unsupported claims

## 9. Citation Requirement

For RAG answers, the answer should be grounded in retrieved context.

Controls:

- require citations
- flag answers without citations
- show source chunks
- indicate when context is insufficient
- avoid answering from model memory for document-specific questions

## 10. Audit Logging

Log important actions:

- login
- document upload
- document deletion
- RAG question
- LLM response
- compliance result
- portfolio upload
- admin action

Audit log fields:

- id
- user_id
- action
- resource_type
- resource_id
- timestamp
- request_id
- status
- metadata

## 11. Secrets Management

Never hardcode secrets.

Use environment variables locally.

In cloud, use:

- AWS Secrets Manager
- Azure Key Vault
- Kubernetes Secrets
- sealed secrets if needed

Secrets include:

- database password
- JWT secret
- LLM API key
- object storage credentials

## 12. Threat Model

### Threat: Unauthorized document access

Mitigation:

- RBAC
- document ownership checks
- audit logs

### Threat: Prompt injection

Mitigation:

- input scanner
- system prompt isolation
- compliance checks

### Threat: PII leakage

Mitigation:

- PII detection
- output masking
- audit trail

### Threat: Hallucinated financial claims

Mitigation:

- RAG grounding
- citation validation
- unsupported claim warning

### Threat: LLM API key leakage

Mitigation:

- secrets manager
- no keys in logs
- no keys in frontend

## 13. Compliance Statuses

### SAFE

The answer has citations and no detected risks.

### NEEDS_REVIEW

The answer may contain risky financial language, weak citation support, or possible sensitive content.

### BLOCKED

The answer contains unsafe content, serious PII exposure, or malicious prompt injection attempt.

## 14. Interview Explanation

Say this:

"Because the project targets financial services, I designed the AI layer with compliance guardrails. The system does not blindly return LLM output. It checks for prompt injection, PII exposure, missing citations, unsupported claims, and financial advice risk. Every important action is stored in audit logs, which is important in regulated environments."