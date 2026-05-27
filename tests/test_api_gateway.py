from pathlib import Path
import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

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


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(_create_test_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "api-gateway",
        "environment": "test",
    }
    assert "X-Request-ID" in response.headers


def test_ready_endpoint_returns_ready_when_checks_pass(monkeypatch) -> None:
    async def fake_check_service_connections(settings):
        return {
            "postgresql": {"status": "ok"},
            "redis": {"status": "ok"},
            "qdrant": {"status": "ok"},
        }

    monkeypatch.setattr(
        "app.api.routes.check_service_connections",
        fake_check_service_connections,
    )

    client = TestClient(_create_test_app())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_endpoint_returns_503_when_a_check_fails(monkeypatch) -> None:
    async def fake_check_service_connections(settings):
        return {
            "postgresql": {"status": "ok"},
            "redis": {"status": "ok"},
            "qdrant": {"status": "error", "detail": "connection failed"},
        }

    monkeypatch.setattr(
        "app.api.routes.check_service_connections",
        fake_check_service_connections,
    )

    client = TestClient(_create_test_app())

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_global_exception_handler_returns_safe_error() -> None:
    app = _create_test_app()

    @app.get("/boom")
    async def boom():
        raise RuntimeError("sensitive internal detail")

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_server_error"
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "sensitive internal detail" not in response.text


def _create_test_app() -> FastAPI:
    settings = Settings(
        DATABASE_URL="postgresql://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
        QDRANT_URL="http://localhost:6333",
        OBJECT_STORAGE_URL="http://localhost:9000",
        JWT_SECRET="test-secret",
        LLM_PROVIDER="mock",
        LLM_API_KEY="test-key",
        APP_ENV="test",
    )
    return create_app(settings)
