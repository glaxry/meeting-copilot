# Day1 Version Record: v0.1.0

## Version goal

Finish the Day1 deliverables from the course plan:

- initialize the repository
- define the Conda environment
- scaffold the C++ / pybind11 boundary
- boot a FastAPI service
- expose the first health and transcription APIs
- establish documentation and testing conventions for later iterations

## What is included

### 1. Project skeleton

- `cpp/` contains the native extension scaffold
- `python/meeting_copilot/` contains the FastAPI service and Day1 transcription service
- `scripts/` contains environment, API, and test helper scripts
- `docs/` contains version, setup, and testing notes
- `tests/` contains API-level regression coverage

### 2. API contract

This version exposes:

- `GET /health`
- `POST /transcribe`

`/transcribe` currently parses WAV metadata and returns either:

- an annotation-backed transcript from `data/annotations/<filename>.txt`, or
- a deterministic mock transcript if no annotation is available

This gives Day1 a stable JSON interface before the real `whisper.cpp` inference path is connected.

### 3. Native boundary

The native Day1 extension does not yet perform speech recognition. Its role in this version is to:

- validate the CMake + pybind11 build path
- provide runtime metadata back to Python
- mark the exact integration point for native audio logic in later versions

The Day1 native build was verified successfully and the `/health` endpoint can now auto-detect the built module from `build/cpp/Release`.

## Technical decisions

### Why keep a mock backend on Day1

Day1 is about getting the pipeline online end-to-end. A deterministic mock backend keeps the API shape stable while avoiding premature coupling to external model downloads before the base service, tests, and repository process are in place.

### Why keep annotation fallback

Annotation-backed transcripts let us demonstrate realistic meeting outputs during manual demos without changing the API format later.

### Why define Conda immediately

The user requested that Python work run inside a Conda environment. The repository therefore includes environment bootstrap scripts from the first version instead of adding them later.

### Why avoid `conda run` in helper scripts

On this machine, `conda run` hit an encoding-related output bug in the terminal session. The Day1 helper scripts therefore call the environment's `python.exe` directly, which still satisfies the requirement to run inside the Conda environment while being more stable under the current Windows console setup.

## Verified results

- Miniconda installed locally at `.miniconda3/`
- Conda environment `meeting-copilot-day1` created successfully
- `pytest` passed: `3 passed, 1 warning`
- `uvicorn` startup verified with `/health`
- CMake configure and Release build both passed
- `/health` reports `cpp_backend_available: true` after the native module is built

## Known limits

- `whisper.cpp` is not wired into the request path yet
- only WAV uploads are accepted
- no frontend route is served yet
- transcript text is still mock-based unless an annotation sidecar is provided

## Next version target

The next iteration should focus on moving from skeleton to real inference:

- vendor or fetch `whisper.cpp`
- attach real audio-to-text execution to `/transcribe`
- add a sample WAV plus transcript fixture for manual demos
- begin the C++ audio preprocessing path planned for Day2
