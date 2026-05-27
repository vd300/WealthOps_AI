from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
import os
import sys
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from starlette.datastructures import Headers, UploadFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api-gateway"))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("OBJECT_STORAGE_URL", "http://localhost:9000")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("APP_ENV", "test")

from app.core.config import Settings
from app.main import create_app
from app.models.documents import DocumentRecord, DocumentStatus, DocumentUploadResponse
from app.services.chunking import DocumentChunker
from app.services.text_extraction import ExtractedPage, extract_text_pages, flatten_pages


def test_upload_endpoint_accepts_supported_document(monkeypatch) -> None:
    class FakeIngestionService:
        def __init__(self, *, settings):
            self.settings = settings

        async def ingest_upload(self, *, file, uploaded_by):
            now = datetime.now(UTC)
            return DocumentUploadResponse(
                document=DocumentRecord(
                    id=uuid4(),
                    filename=file.filename,
                    content_type=file.content_type,
                    status=DocumentStatus.INDEXED,
                    uploaded_by=uploaded_by,
                    file_size_bytes=27,
                    storage_bucket="wealthops-documents",
                    object_key="documents/doc/example.txt",
                    chunk_count=1,
                    extracted_char_count=27,
                    created_at=now,
                    updated_at=now,
                ),
                ingestion_job_id=uuid4(),
            )

    monkeypatch.setattr("app.api.routes.DocumentIngestionService", FakeIngestionService)

    client = TestClient(_create_test_app())
    response = client.post(
        "/documents/upload",
        files={"file": ("example.txt", b"Revenue increased in 2025.", "text/plain")},
        headers={"X-Uploaded-By": "analyst-1"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["filename"] == "example.txt"
    assert body["document"]["status"] == "INDEXED"
    assert body["document"]["uploaded_by"] == "analyst-1"


def test_upload_validation_rejects_unsupported_file_type() -> None:
    client = TestClient(_create_test_app())

    response = client.post(
        "/documents/upload",
        files={"file": ("malware.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 415


def test_upload_validation_rejects_file_over_size_limit() -> None:
    settings = _settings(DOCUMENT_MAX_FILE_SIZE_BYTES=4)
    client = TestClient(create_app(settings))

    response = client.post(
        "/documents/upload",
        files={"file": ("large.txt", b"12345", "text/plain")},
    )

    assert response.status_code == 413


def test_text_extraction_supports_txt_csv_and_xlsx() -> None:
    txt_pages = extract_text_pages("notes.txt", b"Liquidity risk is elevated.")
    csv_pages = extract_text_pages("holdings.csv", b"ticker,sector\nAAPL,Technology")
    xlsx_pages = extract_text_pages("workbook.xlsx", _xlsx_bytes())

    assert flatten_pages(txt_pages) == "Liquidity risk is elevated."
    assert "ticker, sector" in flatten_pages(csv_pages)
    assert "Sheet: Summary" in flatten_pages(xlsx_pages)
    assert "metric, value" in flatten_pages(xlsx_pages)


def test_text_extraction_supports_pdf() -> None:
    pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"

    pages = extract_text_pages(str(pdf_path), pdf_path.read_bytes())

    assert pages[0].page_number == 1
    assert "Liquidity risk" in flatten_pages(pages)


def test_chunking_uses_configurable_size_overlap_and_page_numbers() -> None:
    chunker = DocumentChunker(chunk_size=10, chunk_overlap=3)
    chunks = chunker.chunk_pages(
        [ExtractedPage(page_number=7, text="abcdefghijklmnopqrstuvwxyz")]
    )

    assert [chunk.content for chunk in chunks] == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]
    assert [chunk.page_number for chunk in chunks] == [7, 7, 7, 7]


@pytest.mark.asyncio
async def test_ingestion_service_updates_status_to_failed(monkeypatch) -> None:
    from app.services import document_ingestion
    from app.services.document_ingestion import DocumentIngestionService

    class FakeRepository:
        def __init__(self):
            now = datetime.now(UTC)
            self.document = DocumentRecord(
                id=uuid4(),
                filename="bad.txt",
                content_type="text/plain",
                status=DocumentStatus.UPLOADED,
                uploaded_by="analyst",
                file_size_bytes=3,
                created_at=now,
                updated_at=now,
            )
            self.transitions = []

        async def create_document(self, **kwargs):
            return self.document

        async def create_ingestion_job(self, document_id):
            return uuid4()

        async def update_document_storage(self, **kwargs):
            return self.document

        async def mark_processing(self, **kwargs):
            self.transitions.append(DocumentStatus.PROCESSING)

        async def mark_failed(self, **kwargs):
            self.transitions.append(DocumentStatus.FAILED)
            return self.document.model_copy(update={"status": DocumentStatus.FAILED})

    class FakeStorage:
        bucket = "wealthops-documents"

        def put_object(self, **kwargs):
            return None

    class FakeVectorStore:
        async def ensure_collection(self):
            return None

    repository = FakeRepository()
    monkeypatch.setattr(document_ingestion, "run_migrations", _noop_migration)
    monkeypatch.setattr(
        document_ingestion,
        "extract_text_pages",
        lambda filename, data: (_ for _ in ()).throw(ValueError("extraction failed")),
    )

    service = DocumentIngestionService(
        settings=_settings(),
        repository=repository,
        storage=FakeStorage(),
        vector_store=FakeVectorStore(),
    )

    result = await service.ingest_upload(
        file=UploadFile(
            filename="bad.txt",
            file=BytesIO(b"bad"),
            headers=Headers({"content-type": "text/plain"}),
        ),
        uploaded_by="analyst",
    )

    assert result.document.status == DocumentStatus.FAILED
    assert repository.transitions == [DocumentStatus.PROCESSING, DocumentStatus.FAILED]


def _xlsx_bytes() -> bytes:
    from io import BytesIO

    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Summary"
    worksheet.append(["metric", "value"])
    worksheet.append(["revenue", "100"])
    data = BytesIO()
    workbook.save(data)
    return data.getvalue()


async def _noop_migration(settings) -> None:
    return None


def _create_test_app() -> FastAPI:
    return create_app(_settings())


def _settings(**overrides) -> Settings:
    values = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "OBJECT_STORAGE_URL": "http://localhost:9000",
        "JWT_SECRET": "test-secret",
        "LLM_PROVIDER": "mock",
        "LLM_API_KEY": "test-key",
        "APP_ENV": "test",
    }
    values.update(overrides)
    return Settings(**values)
