# Meeting Copilot

Meeting Copilot is a modular smart meeting assistant project based on the Day1 scope defined in the course plan:

- C++ for low-latency audio processing and future `whisper.cpp` integration
- Python for API orchestration and NLP pipelines
- FastAPI for service delivery
- pybind11 for the C++ / Python boundary

## Day1 scope

Day1 focuses on getting a working vertical slice online:

- repository and directory layout
- Conda-based Python environment definition
- CMake + pybind11 extension skeleton
- FastAPI service with `/health` and `/transcribe`
- pytest coverage for the initial API surface
- version notes, setup notes, and test notes

## Current Day1 status

This version intentionally keeps the speech backend lightweight:

- `/transcribe` accepts `.wav` uploads
- audio metadata is parsed locally
- transcript text is resolved from `data/annotations/<filename>.txt` when available
- otherwise a deterministic Day1 mock transcript is returned

This lets the project expose a stable API contract on Day1 while keeping the real `whisper.cpp` integration for the next iteration.

## Repository layout

```text
meeting-copilot/
├── cpp/
├── data/
├── docs/
├── experiments/
├── frontend/
├── python/
├── reports/
├── scripts/
├── tests/
├── CMakeLists.txt
├── environment.yml
└── README.md
```

## Conda environment

The project now uses the existing Anaconda installation instead of a repo-local Miniconda copy.

Current machine defaults:

- Anaconda root: `D:\anaconda`
- Conda executable: `D:\anaconda\Scripts\conda.exe`
- Actual project env path resolved by this machine: `C:\Users\11212\.conda\envs\meeting-copilot-day1`

Recommended commands:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_conda_env.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_api.ps1
```

The helper scripts automatically handle this machine's Conda quirks:

- use the existing Anaconda install
- force `--no-plugins --solver classic` for environment creation
- resolve the env Python from either `D:\anaconda\envs` or `C:\Users\11212\.conda\envs`

## API surface

### `GET /health`

Returns service metadata and whether the optional Day1 C++ extension is available.

### `POST /transcribe`

Accepts a `.wav` upload and returns:

- audio metadata
- a transcript segment list
- aggregated full text
- Day1 notes about the active backend

## C++ build

After the Conda environment is ready, configure the C++ extension with CMake:

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

The Day1 extension exports runtime metadata and gives the Python service a clean place to attach future native audio logic.

## Documentation

- Latest version record: `docs/versions/day1-v0.1.1.md`
- Setup notes: `docs/notes/day1-setup-notes.md`
- Test notes: `docs/testing/day1-test-report.md`
