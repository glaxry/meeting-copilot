from importlib import import_module
from pathlib import Path
from typing import Any
import sys


def _candidate_build_dirs() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    return [
        repo_root / "build" / "cpp" / "Release",
        repo_root / "build" / "cpp" / "RelWithDebInfo",
        repo_root / "build" / "cpp" / "Debug",
    ]


def _ensure_native_module_path() -> None:
    for candidate in _candidate_build_dirs():
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.append(candidate_str)


def _get_cpp_module():
    _ensure_native_module_path()

    try:
        return import_module("meeting_copilot_cpp")
    except Exception:
        return None


def get_cpp_runtime_info() -> dict[str, str] | None:
    module = _get_cpp_module()
    if module is None:
        return None

    raw_info = module.runtime_info()
    return {str(key): str(value) for key, value in raw_info.items()}


def analyze_audio_bytes(
    audio_bytes: bytes,
    frame_ms: int = 30,
    energy_threshold: float = 0.015,
    min_speech_ms: int = 240,
    max_silence_ms: int = 180,
) -> dict[str, Any] | None:
    module = _get_cpp_module()
    if module is None or not hasattr(module, "analyze_audio_bytes"):
        return None

    return module.analyze_audio_bytes(
        audio_bytes,
        frame_ms=frame_ms,
        energy_threshold=energy_threshold,
        min_speech_ms=min_speech_ms,
        max_silence_ms=max_silence_ms,
    )


def transcribe_audio_bytes(
    audio_bytes: bytes,
    audio_label: str = "",
    annotation_text: str = "",
    frame_ms: int = 30,
    energy_threshold: float = 0.015,
    min_speech_ms: int = 240,
    max_silence_ms: int = 180,
) -> dict[str, Any] | None:
    module = _get_cpp_module()
    if module is None or not hasattr(module, "transcribe_audio_bytes"):
        return None

    return module.transcribe_audio_bytes(
        audio_bytes,
        audio_label=audio_label,
        annotation_text=annotation_text,
        frame_ms=frame_ms,
        energy_threshold=energy_threshold,
        min_speech_ms=min_speech_ms,
        max_silence_ms=max_silence_ms,
    )
