from typing import Literal

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start_seconds: float = Field(..., ge=0.0)
    end_seconds: float = Field(..., ge=0.0)
    text: str = Field(..., min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AudioMetadata(BaseModel):
    filename: str
    format: Literal["wav"]
    duration_seconds: float = Field(..., ge=0.0)
    sample_rate_hz: int = Field(..., gt=0)
    channels: int = Field(..., gt=0)
    frame_count: int = Field(..., ge=0)
    backend: str


class TranscriptionResponse(BaseModel):
    audio: AudioMetadata
    transcript: list[TranscriptSegment]
    full_text: str
    notes: list[str] = Field(default_factory=list)
    mock_backend: bool = True


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    cpp_backend_available: bool
    cpp_backend: dict[str, str] | None = None
