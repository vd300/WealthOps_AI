from fastapi import FastAPI

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, request_logging_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    app = FastAPI(
        title="WealthOps AI API Gateway",
        version="0.1.0",
        description="Phase 1 foundation API Gateway for WealthOps AI.",
    )
    app.state.settings = app_settings

    app.middleware("http")(request_logging_middleware)
    register_exception_handlers(app)
    app.include_router(router)

    return app


app = create_app()
