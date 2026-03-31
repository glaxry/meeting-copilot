# Day1 Test Report

## Planned checks

### API tests

- `GET /health` returns status `ok`
- `POST /transcribe` accepts valid WAV input and returns structured metadata
- `POST /transcribe` rejects invalid WAV bytes with a `400`

### Manual checks

- create or update the Anaconda environment from `environment.yml`
- start `uvicorn`
- open `http://127.0.0.1:8000/docs`
- upload a WAV file to `/transcribe`
- verify the JSON response and backend notes

## Automated results

Executed with:

```powershell
C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe -m pytest
```

Observed result:

```text
3 passed, 1 warning in 1.00s
```

The warning comes from Starlette's current `multipart` import path and does not block Day1 functionality.

## Manual service verification

Executed with the Anaconda environment's Python interpreter and validated through a real HTTP request to `/health`.

Observed response:

```json
{"status":"ok","service":"Meeting Copilot","version":"0.1.0-day1","cpp_backend_available":true,"cpp_backend":{"backend":"day1-native-skeleton","version":"0.1.0","compiler":"MSVC"}}
```

## Build verification

Executed:

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

Observed result:

- configure succeeded
- Release build succeeded
- produced `build/cpp/Release/meeting_copilot_cpp.cp311-win_amd64.pyd`
