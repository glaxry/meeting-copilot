# Day3 Test Report

## Automated tests

Executed with:

```powershell
C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe -m pytest
```

Observed result:

```text
4 passed, 1 warning in 0.63s
```

The warning comes from Starlette's current multipart import path and does not block Day3.

## Native build verification

Executed:

```powershell
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" -S . -B build -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="C:\Users\11212\.conda\envs\meeting-copilot-day1\python.exe"
"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build --config Release
```

Observed result:

- configure succeeded
- Release build succeeded
- produced `build/cpp/Release/meeting_copilot_cpp.cp311-win_amd64.pyd`

## Health check

Observed `/health` response after build:

```json
{"status":"ok","service":"Meeting Copilot","version":"0.3.0-day3","cpp_backend_available":true,"cpp_backend":{"backend":"day3-native-transcription-bridge","version":"0.3.0","compiler":"MSVC"}}
```

## Functional Day3 check

A synthetic tone/silence/tone WAV sample was posted to `/transcribe` with the filename `annotated_sync.wav`.

Observed result:

- `audio.backend = cpp-day3-pybind+annotation`
- `speech_segment_count = 2`
- `event_count = 4`
- `full_text` matched `data/annotations/annotated_sync.txt`
- the first two events were `partial` then `final`
- a JSON log file was created under `reports/transcriptions/`
