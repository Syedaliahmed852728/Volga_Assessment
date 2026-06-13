from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_job_service
from app.api.schemas import JobStatusResponse, SegmentsResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: str,
    service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    job = service.get_status(job_id)
    result_payload = job.get("result")
    result_model = None
    if result_payload:
        result_model = SegmentsResponse(
            file_hash=result_payload["file_hash"],
            language=result_payload.get("language"),
            text=result_payload["text"],
            duration=result_payload.get("duration"),
            segments=result_payload.get("segments", []),
            cached=True,
        )
    return JobStatusResponse(
        job_id=job["job_id"],
        file_hash=job["file_hash"],
        status=job["status"],
        error=job.get("error"),
        result=result_model,
    )
