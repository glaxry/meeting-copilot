from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import json
import re
from typing import Any
import wave

from meeting_copilot.bridge import (
    analyze_audio_bytes,
    get_cpp_runtime_info,
    transcribe_audio_bytes as native_transcribe_audio_bytes,
)
from meeting_copilot.config import get_settings
from meeting_copilot.schemas import (
    AudioMetadata,
    TranscriptEvent,
    TranscriptSegment,
    TranscriptionLogMetadata,
    TranscriptionResponse,
)


class UnsupportedAudioError(ValueError):
    """Raised when the uploaded file cannot be processed as a supported WAV input."""


@dataclass(frozen=True)
class WaveMetadata:
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    frame_count: int


@dataclass(frozen=True)
class SpeechWindow:
    start_seconds: float
    end_seconds: float
    frame_count: int
    sample_count: int
    average_energy: float


@dataclass(frozen=True)
class AudioAnalysis:
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    frame_count: int
    speech_duration_seconds: float
    speech_segments: list[SpeechWindow]
    backend_name: str


@dataclass(frozen=True)
class TranscriptionPayload:
    audio: AudioMetadata
    transcript: list[TranscriptSegment]
    events: list[TranscriptEvent]
    full_text: str
    notes: list[str]
    mock_backend: bool


class Day3Transcriber:
    def __init__(self, annotations_dir: Path, transcription_logs_dir: Path) -> None:
        self.annotations_dir = annotations_dir
        self.transcription_logs_dir = transcription_logs_dir

    def transcribe(self, filename: str, audio_bytes: bytes) -> TranscriptionResponse:
        annotation_text = self._load_annotation(filename)
        native_result = self._native_transcribe(filename, audio_bytes, annotation_text)
        if native_result is not None:
            payload = self._build_native_payload(filename, native_result)
        else:
            payload = self._build_fallback_payload(filename, audio_bytes, annotation_text)

        log_metadata = self._write_transcription_log(filename, payload)
        notes = list(payload.notes)
        notes.append(f"Stored Day3 transcription log at {log_metadata.relative_path}.")

        return TranscriptionResponse(
            audio=payload.audio,
            transcript=payload.transcript,
            full_text=payload.full_text,
            events=payload.events,
            notes=notes,
            mock_backend=payload.mock_backend,
            log=log_metadata,
        )

    def _native_transcribe(
        self,
        filename: str,
        audio_bytes: bytes,
        annotation_text: str | None,
    ) -> dict[str, Any] | None:
        try:
            return native_transcribe_audio_bytes(
                audio_bytes,
                audio_label=Path(filename).stem,
                annotation_text=annotation_text or "",
            )
        except Exception as exc:
            raise UnsupportedAudioError("Only valid WAV uploads are supported.") from exc

    def _build_native_payload(self, filename: str, native_result: dict[str, Any]) -> TranscriptionPayload:
        transcript = [
            TranscriptSegment(
                start_seconds=round(float(segment["start_seconds"]), 3),
                end_seconds=round(float(segment["end_seconds"]), 3),
                text=str(segment["text"]),
                confidence=round(float(segment["confidence"]), 3),
            )
            for segment in native_result["transcript_segments"]
        ]
        events = [
            TranscriptEvent(
                event_index=int(event["event_index"]),
                chunk_index=int(event["chunk_index"]),
                event_type=str(event["event_type"]),
                start_seconds=round(float(event["start_seconds"]), 3),
                end_seconds=round(float(event["end_seconds"]), 3),
                text=str(event["text"]),
                confidence=round(float(event["confidence"]), 3),
            )
            for event in native_result["transcript_events"]
        ]

        mock_backend = bool(native_result["mock_backend"])
        backend_suffix = "mock" if mock_backend else "annotation"
        notes = [str(note) for note in native_result.get("notes", [])]
        cpp_runtime_info = get_cpp_runtime_info()
        if cpp_runtime_info:
            notes.append(
                f"Detected native extension compiled with {cpp_runtime_info.get('compiler', 'unknown compiler')}."
            )
        notes.append(f"Python received {len(events)} incremental transcription event(s) from the native bridge.")

        return TranscriptionPayload(
            audio=AudioMetadata(
                filename=filename,
                format="wav",
                duration_seconds=round(float(native_result["duration_seconds"]), 3),
                sample_rate_hz=int(native_result["sample_rate_hz"]),
                channels=int(native_result["channels"]),
                frame_count=int(native_result["total_frame_count"]),
                speech_segment_count=len(native_result["speech_segments"]),
                speech_duration_seconds=round(float(native_result["speech_duration_seconds"]), 3),
                backend=f"{native_result['backend_name']}+{backend_suffix}",
            ),
            transcript=transcript,
            events=events,
            full_text=self._normalize_text(str(native_result["full_text"])),
            notes=notes,
            mock_backend=mock_backend,
        )

    def _build_fallback_payload(
        self,
        filename: str,
        audio_bytes: bytes,
        annotation_text: str | None,
    ) -> TranscriptionPayload:
        analysis, notes = self._analyze_audio(audio_bytes)
        windows = self._display_windows(analysis)

        if annotation_text:
            annotation_path = self.annotations_dir / f"{Path(filename).stem}.txt"
            notes.append(f"Loaded transcript from {annotation_path.relative_to(get_settings().repo_root)}.")
            notes.append("Day3 fallback distributed annotation text across the detected speech windows.")
            transcript = self._build_annotation_segments(annotation_text, windows)
            mock_backend = False
        else:
            notes.append("No annotation sidecar was found, so Day3 fallback generated mock transcript text.")
            transcript = self._build_mock_segments(filename, windows)
            mock_backend = True

        events = self._build_transcript_events(transcript)
        notes.append(f"Day3 fallback emitted {len(events)} incremental transcription event(s).")

        if analysis.backend_name.startswith("cpp"):
            cpp_runtime_info = get_cpp_runtime_info()
            if cpp_runtime_info:
                notes.append(
                    f"Detected native extension compiled with {cpp_runtime_info.get('compiler', 'unknown compiler')}."
                )

        return TranscriptionPayload(
            audio=AudioMetadata(
                filename=filename,
                format="wav",
                duration_seconds=round(analysis.duration_seconds, 3),
                sample_rate_hz=analysis.sample_rate_hz,
                channels=analysis.channels,
                frame_count=analysis.frame_count,
                speech_segment_count=len(analysis.speech_segments),
                speech_duration_seconds=round(analysis.speech_duration_seconds, 3),
                backend=f"{analysis.backend_name}+{'mock' if mock_backend else 'annotation'}",
            ),
            transcript=transcript,
            events=events,
            full_text=self._full_text_from_segments(transcript),
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
            raise UnsupportedAudioError("Only valid WAV uploads are supported.") from exc

        if sample_rate_hz <= 0:
            raise UnsupportedAudioError("Uploaded WAV file has an invalid sample rate.")

        duration_seconds = frame_count / sample_rate_hz if frame_count else 0.0
        return WaveMetadata(
            duration_seconds=duration_seconds,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
            frame_count=frame_count,
        )

    def _analyze_audio(self, audio_bytes: bytes) -> tuple[AudioAnalysis, list[str]]:
        notes: list[str] = []
        try:
            native_result = analyze_audio_bytes(audio_bytes)
        except Exception as exc:
            raise UnsupportedAudioError("Only valid WAV uploads are supported.") from exc

        if native_result is not None:
            return self._parse_native_analysis(native_result), notes

        metadata = self._read_wave_metadata(audio_bytes)
        notes.append("Native C++ module was not available, so Day3 fell back to Python WAV metadata parsing.")
        full_window = SpeechWindow(
            start_seconds=0.0,
            end_seconds=metadata.duration_seconds,
            frame_count=metadata.frame_count,
            sample_count=metadata.frame_count,
            average_energy=0.0,
        )
        return AudioAnalysis(
            duration_seconds=metadata.duration_seconds,
            sample_rate_hz=metadata.sample_rate_hz,
            channels=metadata.channels,
            frame_count=metadata.frame_count,
            speech_duration_seconds=metadata.duration_seconds,
            speech_segments=[full_window] if metadata.duration_seconds > 0 else [],
            backend_name="python-day3-fallback",
        ), notes

    def _parse_native_analysis(self, native_result: dict[str, Any]) -> AudioAnalysis:
        speech_segments = [
            SpeechWindow(
                start_seconds=float(segment["start_seconds"]),
                end_seconds=float(segment["end_seconds"]),
                frame_count=int(segment["frame_count"]),
                sample_count=int(segment["sample_count"]),
                average_energy=float(segment["average_energy"]),
            )
            for segment in native_result["speech_segments"]
        ]

        return AudioAnalysis(
            duration_seconds=float(native_result["duration_seconds"]),
            sample_rate_hz=int(native_result["sample_rate_hz"]),
            channels=int(native_result["channels"]),
            frame_count=int(native_result["total_frame_count"]),
            speech_duration_seconds=float(native_result["speech_duration_seconds"]),
            speech_segments=speech_segments,
            backend_name="cpp-day3-analysis",
        )

    def _load_annotation(self, filename: str) -> str | None:
        annotation_path = self.annotations_dir / f"{Path(filename).stem}.txt"
        if not annotation_path.exists():
            return None

        transcript_text = annotation_path.read_text(encoding="utf-8").strip()
        return transcript_text or None

    def _display_windows(self, analysis: AudioAnalysis) -> list[SpeechWindow]:
        if analysis.speech_segments:
            return analysis.speech_segments

        if analysis.duration_seconds <= 0.0:
            return []

        return [
            SpeechWindow(
                start_seconds=0.0,
                end_seconds=analysis.duration_seconds,
                frame_count=analysis.frame_count,
                sample_count=analysis.frame_count,
                average_energy=0.0,
            )
        ]

    def _build_annotation_segments(self, transcript_text: str, windows: list[SpeechWindow]) -> list[TranscriptSegment]:
        if not windows:
            return []

        effective_windows = windows
        target_segment_count = max(1, min(len(windows), self._max_chunk_count(transcript_text)))
        if target_segment_count < len(windows):
            # If the transcript text is too short for every detected speech window,
            # merge adjacent windows so each returned segment still has usable text.
            effective_windows = self._merge_windows(windows, target_segment_count)

        text_chunks = self._split_text_into_chunks(transcript_text, len(effective_windows))
        return [
            TranscriptSegment(
                start_seconds=round(window.start_seconds, 3),
                end_seconds=round(window.end_seconds, 3),
                text=text_chunks[index],
                confidence=self._segment_confidence(window),
            )
            for index, window in enumerate(effective_windows)
        ]

    def _build_mock_segments(self, filename: str, windows: list[SpeechWindow]) -> list[TranscriptSegment]:
        stem = Path(filename).stem
        transcript: list[TranscriptSegment] = []
        for index, window in enumerate(windows):
            transcript.append(
                TranscriptSegment(
                    start_seconds=round(window.start_seconds, 3),
                    end_seconds=round(window.end_seconds, 3),
                    text=(
                        f"Day3 mock speech segment {index + 1} for '{stem}' "
                        f"from {window.start_seconds:.2f}s to {window.end_seconds:.2f}s."
                    ),
                    confidence=self._segment_confidence(window),
                )
            )
        return transcript

    def _build_transcript_events(self, transcript: list[TranscriptSegment]) -> list[TranscriptEvent]:
        events: list[TranscriptEvent] = []
        for index, segment in enumerate(transcript):
            duration_seconds = max(0.0, segment.end_seconds - segment.start_seconds)
            partial_end_seconds = round(segment.start_seconds + duration_seconds * 0.6, 3)
            partial_text = self._partial_text(segment.text)
            events.append(
                TranscriptEvent(
                    event_index=len(events),
                    chunk_index=index,
                    event_type="partial",
                    start_seconds=segment.start_seconds,
                    end_seconds=partial_end_seconds,
                    text=partial_text,
                    confidence=segment.confidence,
                )
            )
            events.append(
                TranscriptEvent(
                    event_index=len(events),
                    chunk_index=index,
                    event_type="final",
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    text=segment.text,
                    confidence=segment.confidence,
                )
            )
        return events

    def _partial_text(self, text: str) -> str:
        normalized = self._normalize_text(text)
        words = normalized.split()
        if len(words) > 1:
            return " ".join(words[: max(1, len(words) // 2)])
        if len(normalized) <= 1:
            return normalized
        return normalized[: max(1, len(normalized) // 2)]

    def _full_text_from_segments(self, transcript: list[TranscriptSegment]) -> str:
        return self._normalize_text(" ".join(segment.text for segment in transcript))

    def _max_chunk_count(self, transcript_text: str) -> int:
        word_count = len(transcript_text.split())
        if word_count > 0:
            return word_count
        return max(1, len(transcript_text))

    def _split_text_into_chunks(self, transcript_text: str, segment_count: int) -> list[str]:
        cleaned_text = self._normalize_text(transcript_text)
        if segment_count <= 1:
            return [cleaned_text]

        words = cleaned_text.split(" ")
        if len(words) >= segment_count:
            items = words
            joiner = " "
        else:
            items = list(cleaned_text)
            joiner = ""

        chunks: list[str] = []
        item_count = len(items)
        for index in range(segment_count):
            start = round(index * item_count / segment_count)
            end = round((index + 1) * item_count / segment_count)
            chunk = joiner.join(items[start:end]).strip()
            if not chunk:
                chunk = chunks[-1] if chunks else cleaned_text
            chunks.append(chunk)
        return chunks

    def _merge_windows(self, windows: list[SpeechWindow], target_count: int) -> list[SpeechWindow]:
        if target_count >= len(windows):
            return windows

        merged: list[SpeechWindow] = []
        for index in range(target_count):
            start = round(index * len(windows) / target_count)
            end = round((index + 1) * len(windows) / target_count)
            bucket = windows[start:end]
            if not bucket:
                continue

            average_energy = sum(window.average_energy for window in bucket) / len(bucket)
            merged.append(
                SpeechWindow(
                    start_seconds=bucket[0].start_seconds,
                    end_seconds=bucket[-1].end_seconds,
                    frame_count=sum(window.frame_count for window in bucket),
                    sample_count=sum(window.sample_count for window in bucket),
                    average_energy=average_energy,
                )
            )
        return merged

    def _segment_confidence(self, window: SpeechWindow) -> float:
        confidence = 0.55 + window.average_energy * 4.0
        return round(max(0.2, min(0.99, confidence)), 3)

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def _write_transcription_log(
        self,
        filename: str,
        payload: TranscriptionPayload,
    ) -> TranscriptionLogMetadata:
        settings = get_settings()
        self.transcription_logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc)
        log_id = f"{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}_{self._slugify(Path(filename).stem)}"
        log_path = self.transcription_logs_dir / f"{log_id}.json"

        log_payload = {
            "log_id": log_id,
            "created_at_utc": timestamp.isoformat().replace("+00:00", "Z"),
            "source_filename": filename,
            "audio": payload.audio.model_dump(),
            "transcript": [segment.model_dump() for segment in payload.transcript],
            "events": [event.model_dump() for event in payload.events],
            "full_text": payload.full_text,
            "notes": payload.notes,
            "mock_backend": payload.mock_backend,
        }
        log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return TranscriptionLogMetadata(
            log_id=log_id,
            relative_path=log_path.relative_to(settings.repo_root).as_posix(),
            event_count=len(payload.events),
        )

    def _slugify(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
        cleaned = cleaned.strip("-")
        return cleaned or "transcript"


@lru_cache(maxsize=1)
def get_transcriber() -> Day3Transcriber:
    settings = get_settings()
    return Day3Transcriber(
        annotations_dir=settings.annotations_dir,
        transcription_logs_dir=settings.transcription_logs_dir,
    )
