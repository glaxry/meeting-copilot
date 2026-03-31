from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from meeting_copilot.schemas import TranscriptionResponse
from meeting_copilot.services.transcription import UnsupportedAudioError, get_transcriber

router = APIRouter(tags=["transcription"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: Annotated[UploadFile, File(description="Upload a WAV file for Day3 transcription.")]
) -> TranscriptionResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")

    raw_audio = await file.read()
    if not raw_audio:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return get_transcriber().transcribe(file.filename, raw_audio)
    except UnsupportedAudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
