from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, description="Research and decision-support platform for reproducible hybrid quantum-classical biomedical ML.")
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": "The request could not be completed.", "details": None})
    return app
app = create_app()
