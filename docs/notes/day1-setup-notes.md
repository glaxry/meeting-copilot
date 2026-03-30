# Day1 Setup Notes

## Source document summary

The planning document defines the project as a 7-day modular smart meeting assistant with this architecture:

- C++ for performance-sensitive audio handling
- Python for LLM and NLP orchestration
- FastAPI for backend APIs
- pybind11 for language interop

Day1 specifically requires the repository, environment, CMake + pybind11 setup, a basic FastAPI service, and a first working `/health` or `/transcribe` endpoint.

## Local machine observations

The current machine already has:

- Visual Studio 2022 Professional
- `cmake.exe` at `C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe`
- `cl.exe` at `C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC\14.32.31326\bin\Hostx64\x64\cl.exe`
- `VsDevCmd.bat` at `C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\Tools\VsDevCmd.bat`

The current machine does not expose the following on `PATH`:

- `conda`
- `python`
- `cmake`
- `cl`

So Day1 provisions a repository-local Miniconda install inside the workspace.

## Environment outcomes

- local Miniconda installed successfully at `.miniconda3/`
- Conda environment `meeting-copilot-day1` created successfully
- FastAPI, pytest, pybind11, and upload dependencies installed successfully
- native extension configured and built successfully with Visual Studio 2022

## Design notes for Day1

### API-first

The project starts from a stable API contract instead of waiting for the full native speech stack. This is the fastest path to a testable service.

### Mock transcript instead of fake complexity

It is better to expose a transparent mock backend than to pretend a placeholder is real speech recognition. The response payload explicitly marks whether the backend is mock-based.

### Native code starts narrow

The initial native module only returns runtime metadata. This keeps the pybind11 and CMake path narrow enough to debug before the real audio pipeline is attached.

### Console-specific workaround

`conda run` hit a Windows console encoding bug in this session. Day1 therefore uses the environment's `python.exe` directly for tests and service startup. That still runs the project inside the Conda environment while avoiding the unstable output path.

## Immediate follow-up items

- vendor or clone `whisper.cpp`
- replace the mock transcript path with real inference
- add a real sample WAV for demos
- start the Day2 C++ audio preprocessing implementation
