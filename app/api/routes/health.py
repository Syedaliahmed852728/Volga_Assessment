from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.config import settings
from app.core.device import resolve_device

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.whisper_model,
        device=resolve_device(settings.device),
    )
