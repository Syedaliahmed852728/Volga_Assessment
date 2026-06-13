from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Segment(BaseModel):
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Segment duration in seconds")
    text: str = Field(..., description="Recognized text for the segment")


class TranscriptionResponse(BaseModel):
    file_hash: str
    language: Optional[str] = None
    text: str
    duration: Optional[float] = None
    cached: bool = False


class SegmentsResponse(TranscriptionResponse):
    segments: list[Segment] = Field(default_factory=list)


class JobCreatedResponse(BaseModel):
    job_id: str
    file_hash: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    file_hash: Optional[str] = None
    status: str
    error: Optional[str] = None
    result: Optional[SegmentsResponse] = None


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
