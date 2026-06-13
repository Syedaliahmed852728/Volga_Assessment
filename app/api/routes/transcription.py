from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies import (
    get_audio_service,
    get_job_service,
    get_storage,
    get_transcription_service,
)
from app.api.schemas import (
    JobCreatedResponse,
    SegmentsResponse,
    TranscriptionResponse,
)
from app.config import settings
from app.core.exceptions import FileTooLargeError, InvalidUploadError
from app.repositories.file_storage import FileStorage
from app.services.audio_service import AudioService
from app.services.job_service import JobService
from app.services.transcription_service import TranscriptionService

router = APIRouter(prefix="/transcribe", tags=["transcription"])


def _persist_upload(
    audio: UploadFile,
    audio_service: AudioService,
    storage: FileStorage,
) -> tuple[Path, str]:
    if not audio.filename:
        raise InvalidUploadError("Missing filename")
    audio_service.validate_extension(audio.filename)
    if audio.size is not None and audio.size > settings.max_upload_mb * 1024 * 1024:
        raise FileTooLargeError(f"File exceeds {settings.max_upload_mb} MB limit")
    return storage.save_upload(audio.file, audio.filename)


@router.post("", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    audio_service: AudioService = Depends(get_audio_service),
    storage: FileStorage = Depends(get_storage),
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResponse:
    raw_path, file_hash = _persist_upload(audio, audio_service, storage)

    cached = service.get_cached(file_hash)
    if cached:
        return TranscriptionResponse(
            file_hash=file_hash,
            language=cached["language"],
            text=cached["text"],
            duration=cached.get("duration"),
            cached=True,
        )

    result = await run_in_threadpool(service.transcribe, raw_path, file_hash)
    return TranscriptionResponse(
        file_hash=file_hash,
        language=result["language"],
        text=result["text"],
        duration=result.get("duration"),
        cached=False,
    )


@router.post("/segments", response_model=SegmentsResponse)
async def transcribe_with_segments(
    audio: UploadFile = File(...),
    audio_service: AudioService = Depends(get_audio_service),
    storage: FileStorage = Depends(get_storage),
    service: TranscriptionService = Depends(get_transcription_service),
) -> SegmentsResponse:
    raw_path, file_hash = _persist_upload(audio, audio_service, storage)

    cached = service.get_cached(file_hash)
    if cached:
        return SegmentsResponse(
            file_hash=file_hash,
            language=cached["language"],
            text=cached["text"],
            duration=cached.get("duration"),
            segments=cached.get("segments", []),
            cached=True,
        )

    result = await run_in_threadpool(service.transcribe, raw_path, file_hash)
    return SegmentsResponse(
        file_hash=file_hash,
        language=result["language"],
        text=result["text"],
        duration=result.get("duration"),
        segments=result.get("segments", []),
        cached=False,
    )


@router.post("/async", response_model=JobCreatedResponse)
async def transcribe_async(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    audio_service: AudioService = Depends(get_audio_service),
    storage: FileStorage = Depends(get_storage),
    job_service: JobService = Depends(get_job_service),
) -> JobCreatedResponse:
    raw_path, file_hash = _persist_upload(audio, audio_service, storage)
    job_id = job_service.enqueue(file_hash)
    background_tasks.add_task(job_service.run, job_id, raw_path, file_hash)
    return JobCreatedResponse(job_id=job_id, file_hash=file_hash, status="pending")
