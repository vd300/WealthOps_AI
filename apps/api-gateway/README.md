# API Gateway

FastAPI service that currently provides Phase 1 foundation endpoints.

## Endpoints

- `GET /health`
- `GET /ready`

## Run Locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the service:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service requires configuration from environment variables. See the repository `.env.example`.

## Phase Boundary

This service does not include authentication, document upload, RAG, portfolio, or compliance APIs yet.
