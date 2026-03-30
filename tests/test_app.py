import io
import math
import wave

from fastapi.testclient import TestClient

from meeting_copilot.app import app


client = TestClient(app)


def build_test_wav(duration_seconds: float = 1.0, sample_rate_hz: int = 16000) -> bytes:
    sample_count = int(duration_seconds * sample_rate_hz)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate_hz)

        frames = bytearray()
        for index in range(sample_count):
            amplitude = int(12000 * math.sin(2 * math.pi * 440 * index / sample_rate_hz))
            frames.extend(amplitude.to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(bytes(frames))

    return buffer.getvalue()


def test_health_endpoint_reports_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Meeting Copilot"
    assert payload["version"] == "0.1.0-day1"


def test_transcribe_endpoint_returns_structured_day1_payload() -> None:
    audio_bytes = build_test_wav(duration_seconds=1.25)

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
    assert payload["audio"]["duration_seconds"] == 1.25
    assert payload["transcript"][0]["text"].startswith("Day1 mock transcript")
    assert payload["mock_backend"] is True


def test_transcribe_endpoint_rejects_invalid_audio() -> None:
    response = client.post(
        "/transcribe",
        files={"file": ("broken.wav", b"not-a-real-wave-file", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Day1 only supports valid WAV uploads."
