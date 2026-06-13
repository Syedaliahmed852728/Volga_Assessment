from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from app.core.exceptions import JobNotFoundError
from app.repositories.job_repository import JobRepository
from app.services.transcription_service import TranscriptionService


class JobService:
    def __init__(
        self,
        repository: JobRepository,
        transcription_service: TranscriptionService,
    ) -> None:
        self.repository = repository
        self.transcription_service = transcription_service

    def enqueue(self, file_hash: str) -> str:
        job_id = uuid.uuid4().hex
        self.repository.create(job_id, file_hash)
        return job_id

    def run(self, job_id: str, raw_path: Path, file_hash: str) -> None:
        self.repository.update_status(job_id, "processing")
        try:
            self.transcription_service.transcribe(raw_path, file_hash)
        except Exception as exc:
            self.repository.update_status(job_id, "failed", str(exc))
            return
        self.repository.update_status(job_id, "done")

    def get_status(self, job_id: str) -> dict:
        job = self.repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")

        result: Optional[dict] = None
        if job["status"] == "done" and job["file_hash"]:
            result = self.transcription_service.get_cached(job["file_hash"])
        return {**job, "result": result}
