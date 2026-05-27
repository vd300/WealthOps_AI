from uuid import UUID

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.db.documents import DocumentRepository
from app.db.migrations import run_migrations
from app.models.documents import DocumentListResponse, DocumentRecord, DocumentUploadResponse
from app.models.rag import RAGQueryRequest, RAGQueryResponse
from app.services.document_ingestion import DocumentIngestionService
from app.services.health import check_service_connections
from app.services.rag import RAGQueryService

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.app_env,
    }


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    checks = await check_service_connections(settings)
    is_ready = all(check["status"] == "ok" for check in checks.values())

    response_status = (
        status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=response_status,
        content={
            "status": "ready" if is_ready else "not_ready",
            "service": settings.service_name,
            "checks": checks,
        },
    )


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index a document",
    description=(
        "Uploads a supported document and returns the UUID used by APIs. "
        "A frontend would show filenames to users, but API calls use document_id UUIDs."
    ),
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    uploaded_by: str = Header(default="local-user", alias="X-Uploaded-By"),
) -> DocumentUploadResponse:
    service = DocumentIngestionService(settings=request.app.state.settings)
    return await service.ingest_upload(file=file, uploaded_by=uploaded_by)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
    description=(
        "Returns uploaded document metadata. Use the document id from this response as "
        "document_ids[] in POST /rag/query; user interfaces can show filenames while APIs use UUIDs."
    ),
)
async def list_documents(request: Request) -> DocumentListResponse:
    settings = request.app.state.settings
    await run_migrations(settings)
    repository = DocumentRepository(settings)
    documents = await repository.list_documents()
    return DocumentListResponse(documents=documents)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentRecord,
    summary="Get uploaded document details",
    description=(
        "Returns details for one uploaded document UUID, including filename, status, "
        "chunk_count, and any ingestion error message."
    ),
)
async def get_document(request: Request, document_id: UUID) -> DocumentRecord:
    settings = request.app.state.settings
    await run_migrations(settings)
    repository = DocumentRepository(settings)
    document = await repository.get_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Document id '{document_id}' was not found. Use GET /documents to copy "
                "a valid document_id UUID before calling POST /rag/query."
            ),
        )
    return document


@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
    summary="Ask a question over indexed documents",
    description=(
        "Ask a RAG question. document_ids must be UUIDs copied from GET /documents. "
        "Frontend clients should display filenames, but APIs keep UUIDs as primary identifiers."
    ),
)
async def query_rag(
    request: Request,
    payload: RAGQueryRequest,
    user_id: str = Header(default="local-user", alias="X-User-ID"),
) -> RAGQueryResponse:
    service = RAGQueryService(settings=request.app.state.settings)
    return await service.query(
        request=payload,
        user_id=user_id,
        request_id=getattr(request.state, "request_id", None),
    )
