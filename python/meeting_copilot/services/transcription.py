from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re
from typing import Any
import wave

from meeting_copilot.bridge import analyze_audio_bytes, get_cpp_runtime_info
from meeting_copilot.config import get_settings
from meeting_copilot.schemas import AudioMetadata, TranscriptSegment, TranscriptionResponse


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


class Day2Transcriber:
    def __init__(self, annotations_dir: Path) -> None:
        self.annotations_dir = annotations_dir

    def transcribe(self, filename: str, audio_bytes: bytes) -> TranscriptionResponse:
        analysis, notes = self._analyze_audio(audio_bytes)
        windows = self._display_windows(analysis)
        annotation_text = self._load_annotation(filename)

        if annotation_text:
            annotation_path = self.annotations_dir / f"{Path(filename).stem}.txt"
            notes.append(f"Loaded transcript from {annotation_path.relative_to(get_settings().repo_root)}.")
            notes.append("Day2 used the native speech windows and distributed annotation text across timestamped segments.")
            mock_backend = False
            transcript = self._build_annotation_segments(annotation_text, windows)
        else:
            notes.append("No matching transcript annotation was found, so Day2 generated mock text over native speech windows.")
            notes.append("The C++ audio pipeline is active, but whisper.cpp text decoding is still scheduled for the next milestone.")
            mock_backend = True
            transcript = self._build_mock_segments(filename, windows)

        cpp_runtime_info = get_cpp_runtime_info()
        backend_name = f"{analysis.backend_name}+{'annotation' if annotation_text else 'mock'}"
        if cpp_runtime_info:
            notes.append(
                f"Detected native extension compiled with {cpp_runtime_info.get('compiler', 'unknown compiler')}."
            )
        notes.append(
            f"Day2 audio pipeline detected {len(windows)} speech segment(s) covering {analysis.speech_duration_seconds:.2f} seconds."
        )

        return TranscriptionResponse(
            audio=AudioMetadata(
                filename=filename,
                format="wav",
                duration_seconds=round(analysis.duration_seconds, 3),
                sample_rate_hz=analysis.sample_rate_hz,
                channels=analysis.channels,
                frame_count=analysis.frame_count,
                speech_segment_count=len(windows),
                speech_duration_seconds=round(analysis.speech_duration_seconds, 3),
                backend=backend_name,
            ),
            transcript=transcript,
            full_text=" ".join(segment.text for segment in transcript),
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
        notes.append("Native C++ module was not available, so Day2 fell back to Python WAV metadata parsing.")
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
            backend_name="python-wave-fallback",
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
            backend_name="cpp-day2-vad",
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
                        f"Day2 mock speech segment {index + 1} for '{stem}' "
                        f"from {window.start_seconds:.2f}s to {window.end_seconds:.2f}s."
                    ),
                    confidence=self._segment_confidence(window),
                )
            )
        return transcript

    def _max_chunk_count(self, transcript_text: str) -> int:
        word_count = len(transcript_text.split())
        if word_count > 0:
            return word_count
        return max(1, len(transcript_text))

    def _split_text_into_chunks(self, transcript_text: str, segment_count: int) -> list[str]:
        cleaned_text = re.sub(r"\s+", " ", transcript_text.strip())
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

    def _segment_confidence(self, window: SpeechWindow) -> float | None:
        if window.average_energy <= 0.0:
            return None
        confidence = 0.55 + window.average_energy * 4.0
        return round(max(0.2, min(0.99, confidence)), 3)


@lru_cache(maxsize=1)
def get_transcriber() -> Day2Transcriber:
    settings = get_settings()
    return Day2Transcriber(annotations_dir=settings.annotations_dir)
