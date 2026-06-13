from __future__ import annotations

from functools import lru_cache

from app.repositories.file_storage import FileStorage
from app.repositories.job_repository import JobRepository
from app.repositories.transcription_repository import TranscriptionRepository
from app.services.audio_service import AudioService
from app.services.job_service import JobService
from app.services.transcription_service import TranscriptionService


@lru_cache(maxsize=1)
def get_audio_service() -> AudioService:
    return AudioService()


@lru_cache(maxsize=1)
def get_storage() -> FileStorage:
    return FileStorage()


@lru_cache(maxsize=1)
def get_transcription_repository() -> TranscriptionRepository:
    return TranscriptionRepository()


@lru_cache(maxsize=1)
def get_job_repository() -> JobRepository:
    return JobRepository()


@lru_cache(maxsize=1)
def get_transcription_service() -> TranscriptionService:
    return TranscriptionService(
        audio_service=get_audio_service(),
        storage=get_storage(),
        repository=get_transcription_repository(),
    )


@lru_cache(maxsize=1)
def get_job_service() -> JobService:
    return JobService(
        repository=get_job_repository(),
        transcription_service=get_transcription_service(),
    )
