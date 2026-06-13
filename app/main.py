from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_audio_service, get_transcription_service
from app.api.routes import health, jobs, transcription
from app.config import settings
from app.core.exceptions import AppException
from app.core.model_loader import get_model
from app.repositories.database import init_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    get_audio_service()
    get_transcription_service()
    get_model()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.exception_handler(AppException)
async def _app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(health.router)
app.include_router(transcription.router)
app.include_router(jobs.router)


def serve() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
