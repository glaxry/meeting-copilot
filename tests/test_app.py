import io
import json
import math
from pathlib import Path
import wave

from fastapi.testclient import TestClient

from meeting_copilot.app import app

REPO_ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_TEXT = (
    REPO_ROOT / "data" / "annotations" / "annotated_sync.txt"
).read_text(encoding="utf-8").strip()

client = TestClient(app)


def build_pattern_wav(sample_rate_hz: int = 16000) -> bytes:
    plan = [
        ("tone", 0.45),
        ("silence", 0.3),
        ("tone", 0.45),
    ]
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate_hz)

        frames = bytearray()
        sample_cursor = 0
        for segment_type, duration_seconds in plan:
            sample_count = int(duration_seconds * sample_rate_hz)
            for _ in range(sample_count):
                if segment_type == "tone":
                    amplitude = int(12000 * math.sin(2 * math.pi * 440 * sample_cursor / sample_rate_hz))
                else:
                    amplitude = 0
                frames.extend(amplitude.to_bytes(2, byteorder="little", signed=True))
                sample_cursor += 1

        wav_file.writeframes(bytes(frames))

    return buffer.getvalue()


def read_log_payload(relative_path: str) -> dict:
    log_path = REPO_ROOT / Path(relative_path)
    assert log_path.exists()
    return json.loads(log_path.read_text(encoding="utf-8"))


def test_health_endpoint_reports_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Meeting Copilot"
    assert payload["version"] == "0.3.0-day3"


def test_transcribe_endpoint_returns_day3_mock_payload_and_log() -> None:
    audio_bytes = build_pattern_wav()

    response = client.post(
        "/transcribe",
        files={"file": ("team_sync.wav", audio_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["audio"]["filename"] == "team_sync.wav"
    assert payload["audio"]["format"] == "wav"
    assert payload["audio"]["sample_rate_hz"] == 16000
    assert payload["audio"]["channels"] == 1
    assert payload["audio"]["duration_seconds"] == 1.2
    assert payload["audio"]["speech_duration_seconds"] > 0.0
    assert payload["audio"]["speech_segment_count"] >= 1
    assert payload["mock_backend"] is True
    assert payload["transcript"][0]["text"].startswith("Day3 mock speech segment")
    assert payload["log"]["relative_path"].startswith("reports/transcriptions/")
    assert payload["log"]["event_count"] == len(payload["events"])
    assert {event["event_type"] for event in payload["events"]} == {"partial", "final"}
    assert any("transcription log" in note.lower() for note in payload["notes"])

    log_payload = read_log_payload(payload["log"]["relative_path"])
    assert log_payload["source_filename"] == "team_sync.wav"
    assert log_payload["mock_backend"] is True
    assert len(log_payload["events"]) == payload["log"]["event_count"]

    if payload["audio"]["backend"].startswith("cpp-day3-pybind"):
        assert payload["audio"]["speech_segment_count"] == 2
        assert payload["transcript"][0]["start_seconds"] < payload["transcript"][1]["start_seconds"]


def test_transcribe_endpoint_uses_annotation_sidecar_and_persists_events() -> None:
    audio_bytes = build_pattern_wav()

    response = client.post(
        "/transcribe",
        files={"file": ("annotated_sync.wav", audio_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["mock_backend"] is False
    assert payload["audio"]["backend"].endswith("+annotation")
    assert payload["full_text"] == ANNOTATION_TEXT
    assert len(payload["events"]) >= len(payload["transcript"])
    assert payload["events"][0]["event_type"] == "partial"
    assert payload["events"][1]["event_type"] == "final"

    log_payload = read_log_payload(payload["log"]["relative_path"])
    assert log_payload["full_text"] == ANNOTATION_TEXT
    assert log_payload["mock_backend"] is False
    assert log_payload["audio"]["backend"] == payload["audio"]["backend"]


def test_transcribe_endpoint_rejects_invalid_audio() -> None:
    response = client.post(
        "/transcribe",
        files={"file": ("broken.wav", b"not-a-real-wave-file", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only valid WAV uploads are supported."
