from importlib import import_module
from pathlib import Path
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


def get_cpp_runtime_info() -> dict[str, str] | None:
    _ensure_native_module_path()

    try:
        module = import_module("meeting_copilot_cpp")
    except Exception:
        return None

    raw_info = module.runtime_info()
    return {str(key): str(value) for key, value in raw_info.items()}
