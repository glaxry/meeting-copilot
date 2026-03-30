from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import wave

from meeting_copilot.bridge import get_cpp_runtime_info
from meeting_copilot.config import get_settings
from meeting_copilot.schemas import AudioMetadata, TranscriptSegment, TranscriptionResponse


class UnsupportedAudioError(ValueError):
    """Raised when the uploaded file cannot be processed as the Day1 WAV input."""


@dataclass(frozen=True)
class WaveMetadata:
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    frame_count: int


class Day1Transcriber:
    def __init__(self, annotations_dir: Path) -> None:
        self.annotations_dir = annotations_dir

    def transcribe(self, filename: str, audio_bytes: bytes) -> TranscriptionResponse:
        metadata = self._read_wave_metadata(audio_bytes)
        transcript_text, mock_backend, notes = self._resolve_transcript(filename, metadata)

        cpp_runtime_info = get_cpp_runtime_info()
        backend_name = "python-day1-mock" if mock_backend else "python-day1-annotation"
        if cpp_runtime_info:
            backend_name = f"{backend_name}+{cpp_runtime_info['backend']}"
            notes.append(
                f"Detected native extension compiled with {cpp_runtime_info.get('compiler', 'unknown compiler')}."
            )

        segment = TranscriptSegment(
            start_seconds=0.0,
            end_seconds=round(metadata.duration_seconds, 3),
            text=transcript_text,
            confidence=None,
        )

        return TranscriptionResponse(
            audio=AudioMetadata(
                filename=filename,
                format="wav",
                duration_seconds=round(metadata.duration_seconds, 3),
                sample_rate_hz=metadata.sample_rate_hz,
                channels=metadata.channels,
                frame_count=metadata.frame_count,
                backend=backend_name,
            ),
            transcript=[segment],
            full_text=transcript_text,
            notes=notes,
            mock_backend=mock_backend,
        )

    def _read_wave_metadata(self, audio_bytes: bytes) -> WaveMetadata:
        try:
            with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
                channels = wav_file.getnchannels()
                sample_rate_hz = wav_file.getframerate()
                frame_count = wav_file.getnframes()
        except wave.Error as exc:
            raise UnsupportedAudioError("Day1 only supports valid WAV uploads.") from exc

        if sample_rate_hz <= 0:
            raise UnsupportedAudioError("Uploaded WAV file has an invalid sample rate.")

        duration_seconds = frame_count / sample_rate_hz if frame_count else 0.0
        return WaveMetadata(
            duration_seconds=duration_seconds,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
            frame_count=frame_count,
        )

    def _resolve_transcript(self, filename: str, metadata: WaveMetadata) -> tuple[str, bool, list[str]]:
        notes: list[str] = []
        annotation_path = self.annotations_dir / f"{Path(filename).stem}.txt"

        if annotation_path.exists():
            transcript_text = annotation_path.read_text(encoding="utf-8").strip()
            if transcript_text:
                notes.append(f"Loaded transcript from {annotation_path.relative_to(get_settings().repo_root)}.")
                notes.append("Replace annotation-based transcripts with whisper.cpp inference in the next version.")
                return transcript_text, False, notes

        notes.append("No matching transcript annotation was found, so Day1 returned a deterministic mock transcript.")
        notes.append("This API contract is stable and will be wired to whisper.cpp after the native backend is integrated.")
        transcript_text = (
            f"Day1 mock transcript for '{Path(filename).stem}'. "
            f"Parsed {metadata.duration_seconds:.2f} seconds of WAV audio successfully."
        )
        return transcript_text, True, notes


@lru_cache(maxsize=1)
def get_transcriber() -> Day1Transcriber:
    settings = get_settings()
    return Day1Transcriber(annotations_dir=settings.annotations_dir)
