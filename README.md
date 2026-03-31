# Meeting Copilot

Meeting Copilot is a modular smart meeting assistant project built around:

- C++ for performance-sensitive audio processing
- Python for API orchestration and future NLP pipelines
- FastAPI for service delivery
- pybind11 for the C++ / Python boundary

## Current milestone: Day2

Day2 completes the first real native audio pipeline on the C++ side:

- WAV decoding in C++
- frame-based energy VAD
- speech segment extraction with timestamp windows
- pybind11 exposure of native analysis results
- FastAPI `/transcribe` returning multiple timestamped text blocks

The text layer is still annotation-backed or mock-generated for now. Real `whisper.cpp` decoding is the next milestone.

## What works now

- `/health` reports the Day2 native backend when the C++ module is built
- `/transcribe` accepts `.wav` uploads
- native C++ code detects voiced segments and their timestamps
- Python maps annotation or mock text onto those segments
- test coverage validates the API contract and native build path

## Repository layout

```text
meeting-copilot/
├── cpp/
│   ├── audio_preprocess.cpp
│   ├── bindings.cpp
│   ├── transcriber.cpp
│   └── CMakeLists.txt
├── data/
├── docs/
├── frontend/
├── python/
├── scripts/
├── tests/
├── CMakeLists.txt
├── environment.yml
└── README.md
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

Returns service metadata and whether the Day2 C++ extension is active.

### `POST /transcribe`

Accepts a `.wav` upload and returns:

- audio metadata
- detected speech segment count and speech duration
- timestamped transcript blocks
- aggregated full text
- backend notes

## C++ build

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

## Documentation

- Latest version record: `docs/versions/day2-v0.2.0.md`
- Day2 notes: `docs/notes/day2-audio-pipeline-notes.md`
- Day2 test report: `docs/testing/day2-test-report.md`
- Day1 history: `docs/versions/day1-v0.1.1.md`
