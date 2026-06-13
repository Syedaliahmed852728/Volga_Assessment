from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config import settings
from app.core.device import resolve_device, supports_fp16
from app.core.exceptions import TranscriptionError
from app.core.model_loader import get_model
from app.repositories.file_storage import FileStorage
from app.repositories.transcription_repository import TranscriptionRepository
from app.services.audio_service import AudioService


class TranscriptionService:
    def __init__(
        self,
        audio_service: AudioService,
        storage: FileStorage,
        repository: TranscriptionRepository,
    ) -> None:
        self.audio_service = audio_service
        self.storage = storage
        self.repository = repository

    def get_cached(self, file_hash: str) -> Optional[dict]:
        return self.repository.get(file_hash)

    def transcribe(self, raw_path: Path, file_hash: str) -> dict:
        cached = self.get_cached(file_hash)
        if cached:
            return cached

        normalized = self.storage.normalized_path(file_hash)
        self.audio_service.normalize(raw_path, normalized)
        duration = self.audio_service.probe_duration(normalized)

        device = resolve_device(settings.device)
        try:
            result = get_model().transcribe(
                str(normalized),
                fp16=settings.fp16 and supports_fp16(device),
                verbose=False,
            )
        except Exception as exc:
            raise TranscriptionError(str(exc)) from exc

        segments = [
            {
                "start": float(s["start"]),
                "end": float(s["end"]),
                "duration": float(s["end"] - s["start"]),
                "text": s["text"].strip(),
            }
            for s in result.get("segments", [])
        ]

        payload = {
            "file_hash": file_hash,
            "language": result.get("language"),
            "text": result.get("text", "").strip(),
            "segments": segments,
            "duration": duration,
        }

        self.repository.save(
            file_hash=file_hash,
            language=payload["language"],
            text=payload["text"],
            segments=segments,
            duration=duration,
        )
        return payload
