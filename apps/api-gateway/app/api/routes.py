from fastapi import APIRouter, File, Header, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.models.documents import DocumentUploadResponse
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
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    uploaded_by: str = Header(default="local-user", alias="X-Uploaded-By"),
) -> DocumentUploadResponse:
    service = DocumentIngestionService(settings=request.app.state.settings)
    return await service.ingest_upload(file=file, uploaded_by=uploaded_by)


@router.post("/rag/query", response_model=RAGQueryResponse)
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
