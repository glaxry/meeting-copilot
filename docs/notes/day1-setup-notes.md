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
- Anaconda at `D:\anaconda`
- `conda.exe` at `D:\anaconda\Scripts\conda.exe`

`conda` is still not exposed on the shell `PATH`, so repository scripts call the Anaconda executable explicitly.

## Environment outcomes

- repository workflow now uses the existing Anaconda installation instead of `.miniconda3`
- the active project environment resolved to `C:\Users\11212\.conda\envs\meeting-copilot-day1`
- `conda` commands are run with `--no-plugins --solver classic` in this session to avoid the local plugin and solver mismatch issues
- helper scripts now search both the Anaconda root envs directory and the user `.conda\envs` directory
- FastAPI, pytest, pybind11, and upload dependencies are managed through the Anaconda environment
- native extension is built against the Anaconda environment's Python interpreter

## Design notes for Day1

### Reuse the machine's Anaconda install

Using the existing Anaconda installation is cleaner than provisioning a second Conda distribution inside the repo. It also matches your stated local setup.

### Handle dynamic env locations

This machine's Conda configuration places named environments under the user profile instead of under `D:\anaconda\envs`. The helper scripts therefore resolve both locations instead of assuming one fixed env root.

### Keep `--no-plugins --solver classic` in automation

This machine's Conda installation triggers a permission failure inside plugin-based virtual package detection under the agent shell. In addition, the configured default solver is `libmamba`, which is unavailable once plugins are disabled. The automation therefore forces `--no-plugins --solver classic`.

## Immediate follow-up items

- vendor or clone `whisper.cpp`
- replace the mock transcript path with real inference
- add a real sample WAV for demos
- start the Day2 C++ audio preprocessing implementation
