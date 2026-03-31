# Meeting Copilot

Meeting Copilot is a modular smart meeting assistant project built around:

- C++ for performance-sensitive audio processing
- Python for API orchestration and future NLP pipelines
- FastAPI for service delivery
- pybind11 for the C++ / Python boundary

## Current milestone: Day3

Day3 completes the first end-to-end pybind11 transcription bridge:

- native C++ audio analysis is still responsible for WAV parsing and VAD
- C++ now also emits transcript segments and incremental transcription events
- Python consumes the native result, persists a transcription log, and serves it through FastAPI
- `/transcribe` returns audio metadata, transcript blocks, incremental events, and log metadata

The text is still annotation-backed or mock-generated. Real `whisper.cpp` decoding remains the next milestone.

## What works now

- `/health` reports the Day3 native backend when the C++ module is built
- `/transcribe` accepts `.wav` uploads
- native C++ code returns timestamped transcript blocks and incremental events through pybind11
- Python stores each transcription run under `reports/transcriptions/`
- test coverage validates mock mode, annotation mode, logs, and invalid audio handling

## Repository layout

```text
meeting-copilot/
+-- cpp/
|   +-- audio_preprocess.cpp
|   +-- bindings.cpp
|   +-- transcriber.cpp
|   +-- CMakeLists.txt
+-- data/
|   +-- annotations/
|   +-- audio/
+-- docs/
|   +-- notes/
|   +-- testing/
|   +-- versions/
+-- frontend/
+-- python/
+-- reports/
|   +-- transcriptions/
+-- scripts/
+-- tests/
+-- CMakeLists.txt
+-- environment.yml
+-- README.md
```

## Conda environment

The project uses the existing Anaconda installation on this machine.

Recommended commands:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_conda_env.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_api.ps1
```

The helper scripts:

- use `D:\anaconda\Scripts\conda.exe`
- force `--no-plugins --solver classic` for environment creation
- resolve the env Python from either `D:\anaconda\envs` or `C:\Users\11212\.conda\envs`

## API surface

### `GET /health`

Returns service metadata and whether the Day3 C++ extension is active.

### `POST /transcribe`

Accepts a `.wav` upload and returns:

- audio metadata
- detected speech segment count and speech duration
- timestamped transcript blocks
- incremental transcript events
- aggregated full text
- backend notes
- log metadata for the persisted JSON artifact

## C++ build

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

## Documentation

- Latest version record: `docs/versions/day3-v0.3.0.md`
- Day3 notes: `docs/notes/day3-pybind-integration-notes.md`
- Day3 test report: `docs/testing/day3-test-report.md`
- Day2 history: `docs/versions/day2-v0.2.0.md`
